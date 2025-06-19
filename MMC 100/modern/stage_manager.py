import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from dataclasses import dataclass, field, fields
from enum import Enum
import time
from time import monotonic

from motors_hal import AxisType, MotorState, Position, MotorEvent, MotorEventType
from stage_controller import StageControl
from motor_factory import create_driver

from helper import update_stage_position


"""
Made by: Cameron Basara, 6/17/2025

Stage manager, intended to interface with the GUI to give high level commands to the modern stage

TODO:
    Improve config params loading, to consider outside entries
        yaml -> helper functions -> internal storage using dataclasses -> outputs, measurement information
    Clean up existing code, remove gunk, remove duplicates
    Ensure that the other stages behave nicely. Concerned about movement patterns : will they be different logic at different stages?
    Change information access points, loading yaml etcs. Physical ways to store information for next use cases. 
    Implement cominterface ? may not be useful
    Implement interactions with other hardware devices: lasers, detectors, TECs, Cams
    Implement interactions with gui
    Document control flow

"""

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

logger = logging.getLogger(__name__)

STAGE_LIST = [347] # placeholder



class StageManager:
    def __init__(self, config: StageConfiguration):
        self.config = config
        self.motors: Dict[AxisType, StageControl] = {}
        self._event_callbacks: List[Callable[[MotorEvent], None]] = []
        self._last_positions: Dict[AxisType, float] = {}

    # Helper decorator to ensure axis is initialized
    def requires_motor(func):
        """Before method runs, checks is this an axis in self.motors"""
        async def wrapper(self, axis, *args, **kwargs):
            if axis not in self.motors:
                logger.error(f"{axis.name} not initialized")
                return False
            return await func(self, axis, *args, **kwargs)
        return wrapper

    # Helper to catch exceptions
    async def _safe_execute(self, desc: str, coro, default=False):
        """Runs awaits a coroutine passed, try + except log in 1 line"""
        try:
            logger.info(f"{desc}")
            return await coro
        except Exception as e:
            logger.error(f"Error {desc}: {e}")
            logger.debug("Traceback:", exc_info=True)
            return default

    # Helper functions for events
    def add_event_callback(self, callback: Callable[[MotorEvent], None]):
        """Register callback for motor events."""
        self._event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[MotorEvent], None]):
        """Remove event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def _handle_stage_event(self, event: MotorEvent) -> None:
        """Internal meth to forward motor event emitted"""
        for cb in self._event_callbacks:
            try:
                cb(event)
            except Exception as e:
                print(f"[{event.axis.name}] Error in manager-level callback: {e}")

    @update_stage_position
    async def initialize(self, axes):
        """
        Initialize all stage axes
        """
        # Succesful initialization
        results = {}

        for axis in axes:
            # Retrive config
            cfg = self.config

            # Instantiate motors through the the factory
            driver_key = cfg.driver_types[axis]
            params = dict(
                axis=axis,
                com_port=cfg.com_port,
                baudrate=cfg.baudrate,
                timeout=cfg.timeout,
                velocity=cfg.velocities[axis],
                acceleration=cfg.accelerations[axis],
                position_limits=cfg.position_limits[axis],
                position_tolerance=cfg.position_tolerance,
                status_poll_interval=cfg.status_poll_interval
            )
            motor = create_driver(driver_key, **params)

            # Catch exceptions
            ok = await self._safe_execute(f"connect {axis.name}", motor.connect()) # motor connects from abstracted stage driver
            if ok:
                self.motors[axis] = motor
                self._last_positions[axis] = 0.0
                motor.add_event_callback(self._handle_stage_event)
                
            results[axis] = ok

        return all(results.values())

    @update_stage_position
    @requires_motor
    async def home_axis(self, axis: AxisType, direction: int = 0) -> bool:
        ok = await self._safe_execute(f"home {axis.name}", self.motors[axis].home(direction))
       
        # # Wait for home to complete
        # while self.motors[axis]._move_in_progress:
        #     await asyncio.sleep(0.1)
        
        if ok:
            self._last_positions[axis] = 0.0
        return ok
    
    @update_stage_position
    @requires_motor
    async def home_limits(self, axis: AxisType) -> bool:
        if (axis == AxisType.Z):
            # Ensure safe homing of Z axis
            aok = await self._safe_execute(f"", self.motors[AxisType.Y].move_absolute(
                self.config.position_limits[AxisType.Y][1],
                wait_for_completion=True
            ))
            if aok:
                pass
            else:
                return False
        ok, pos_lims = await self._safe_execute(f"home {axis.name} limits", self.motors[axis].home_limits())
        if ok:
            self.config.position_limits[axis] = pos_lims
        return ok

    @requires_motor
    async def wait_for_home_completion(self, axis: AxisType) -> bool:
        ok = await self._safe_execute(f"home {axis.name} status", self.motors[axis]._wait_for_home_completion())
        return ok
    
    @update_stage_position
    async def load_params(self) -> bool:
        """
        Loads preset params of a stage
        """
        # Check if homed
        for axis, motor in self.motors.items():
            if not self.motors[axis]._is_homed:
                logger.error(f"{axis.name} isn't homed - aborting load of params")
                break

        # Intialize params
        cfg = self.config
        
        # Apply profiles
        for axis, target in cfg.initial_positions.items():
            print(f"axis: {axis.name} target: {target}")
            ok = await self._safe_execute(f"move_absolute {axis.name}",
                    self.motors[axis].move_absolute(target, velocity=cfg.velocities[axis], wait_for_completion=True))
            if not ok:
                return ok
        
        return True
    
    @update_stage_position
    @requires_motor
    async def move_single_axis(self, axis: AxisType, position: float,
                               relative=False, velocity=None,
                               wait_for_completion=True) -> bool:
        """
        Move a single axis command. 

        Args:
            axis[AxisType]: axis you want to move eg. AxisType.X (or something nice like x_axis = AxisType.X)
            position[float]: Desired position for absolute or relative distance (+/-) 
            relative[bool]: False by default, set true if you want to send a relative movement command
            velocity: Optional velocity override, useless right now
            wait_for_completion: If True, wait for move to complete and emit MOVE_COMPLETED event

        Returns:
            Position if successful else False  
        """
        if relative:
            ok = await self._safe_execute(f"move_relative {axis.name}", 
                    self.motors[axis].move_relative(position, velocity, wait_for_completion)) 
            if ok:
                self._last_positions[axis] += position
        else:
            ok = await self._safe_execute(f"move_absolute {axis.name}",
                    self.motors[axis].move_absolute(position, velocity, wait_for_completion))
            if ok:
                self._last_positions[axis] = position
        return ok

    @update_stage_position
    async def move_xy_rel(self, xy_distance: Tuple[float, float], wait_for_completion = True):
        """
        MMC Supports multi-axes movement. Move only xy in tandem for safety. Relative movement
        
        Args:
            xy_distance: (x,y) Distance you want to move in microns 
            wait_for_completion: 
        """
        # Need xy to be initialized
        if (AxisType.X not in self.motors) or (AxisType.Y not in self.motors):
            logger.error(f"Axis XY not initialized")
            return False
        # Move the axis synchronously with asyncio
        tx = asyncio.create_task(
            self._safe_execute(f"move x axis: {xy_distance[0]}",
                                       self.motors[AxisType.X].move_relative(distance=(xy_distance[0]), 
                                                                             wait_for_completion=wait_for_completion)))
        ty = asyncio.create_task(self._safe_execute(f"move x axis: {xy_distance[1]}",
                                       self.motors[AxisType.Y].move_relative(distance=(xy_distance[1]), 
                                                                             wait_for_completion=wait_for_completion)))
        # Wait for each task to finish
        aok, bok = await asyncio.gather(tx, ty)

        # report failure
        if not (aok and bok):
            logger.error(f"move_xy failed: X ok?{aok} Y ok?{bok}")
            return False

        # Update last pos
        self._last_positions[AxisType.X] += xy_distance[0]
        self._last_positions[AxisType.Y] += xy_distance[1]

        return (aok, bok)
    
    @update_stage_position
    async def move_xy_absolute(self, xy_distance: Tuple[float, float], wait_for_completion = True):
        """
        MMC Supports multi-axes movement. Move only xy in tandem for safety. Absolute movement
        
        Args:
            xy_distance: (x,y) Distance you want to move in microns 
            wait_for_completion: key to set for wait for completion, currently only works with key set to True
        """
        # Need xy to be initialized
        if (AxisType.X not in self.motors) or (AxisType.Y not in self.motors):
            logger.error(f"Axis XY not initialized")
            return False
        
        # Move the axis synchronously with asyncio
        tx = asyncio.create_task(
            self._safe_execute(f"move x axis: {xy_distance[0]}",
                                       self.motors[AxisType.X].move_absolute(position=(xy_distance[0]), 
                                                                             wait_for_completion=wait_for_completion)))
        ty = asyncio.create_task(self._safe_execute(f"move x axis: {xy_distance[1]}",
                                       self.motors[AxisType.Y].move_absolute(position=(xy_distance[1]), 
                                                                             wait_for_completion=wait_for_completion)))
        # Wait for each task to finish
        aok, bok = await asyncio.gather(tx, ty)

        # report failure
        if not (aok and bok):
            logger.error(f"move_xy failed: X ok?{aok} Y ok?{bok}")
            return False

        # Update last pos
        self._last_positions[AxisType.X] += xy_distance[0]
        self._last_positions[AxisType.Y] += xy_distance[1]

        return (aok, bok)
    
    @update_stage_position
    @requires_motor
    async def stop_axis(self, axis):
        return await self._safe_execute(f"stop {axis.name}", self.motors[axis].stop())

    @update_stage_position
    async def stop_all_axes(self):
        return {axis: await self.stop_axis(axis) for axis in self.motors}

    @update_stage_position
    async def emergency_stop(self):
        if not self.motors:
            return False
        for axis in AxisType:
            if axis in self.motors:
                await self._safe_execute(f"emergency_stop axis {self.motors[axis]}", self.motors[axis].emergency_stop())
        return True
        
    @requires_motor
    async def get_position(self, axis: AxisType) -> Optional[Position]:
        return await self._safe_execute(f"get_position {axis.name}", self.motors[axis].get_position(), default=None)

    async def get_all_positions(self):
        data = {}
        for axis in AxisType:
            if axis in self.motors:
                pos = await self.get_position(axis)
                data[axis] = pos.actual if pos else 0.0
            else:
                data[axis] = 0.0
        return data

    @requires_motor
    async def get_state(self, axis: AxisType) -> Optional[MotorState]:
        return await self._safe_execute(f"get_state {axis.name}", self.motors[axis].get_state(), default=None)

    async def is_any_axis_moving(self):
        for motor in self.motors.values():
            try:
                if await motor.is_moving():
                    return True
            except:
                pass
        return False

    async def wait_for_all_moves_complete(self, timeout=60.0):
        start = time.time()
        while time.time() - start < timeout:
            if not await self.is_any_axis_moving():
                return True
            await asyncio.sleep(0.1)
        return False

    def get_status(self):
        return {
            'connected': bool(self.motors),
            'initialized_axes': list(self.motors),
            'last_positions': self._last_positions,
            'configuration': self.config.__dict__
        }

    async def disconnect_all(self):
        """Disconnect all motors"""
        for m in self.motors.values():
            await self._safe_execute("disconnect", m.disconnect())
        self.motors.clear()
        self._last_positions.clear()

    @requires_motor
    async def disconnect(self, axis: AxisType):
        """
        Disconnect a single motor

        Args:
            axis[AxisType]: axis you wish to disconnect
        """
        await self._safe_execute("disconnect", axis.disconnect())
        del self.motors[axis]
        del self._last_positions[axis]
