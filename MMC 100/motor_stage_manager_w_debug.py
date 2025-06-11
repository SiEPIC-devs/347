import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import time

from motors_hal import AxisType, MotorState, Position, MotorEvent, MotorEventType
from modern_stage import StageControl
from motor_factory import create_driver

"""
Made by: Cameron Basara, 5/30/2025
(PROTOTYPE)
Stage manager, intended to interface with the GUI to give high level commands to the modern stage

With debug logging

TODO:
    Test core movement capabilties beyond already done testing
    Implement config params loading, consider converting dataclass to yaml
        yaml -> helper functions -> internal storage using dataclasses -> outputs, measurement information
    * Clean up modern stage ? 
    Clean up existing code, remove gunk, remove duplicates
    Change information access points, loading yaml etcs. Physical ways to store information for next use cases. 
    Implement factories for drivers (may be at a different level)
    Implement standardized interactions with hal
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

@dataclass
class StagePosition:
    """
    Current position of stage
    """
    x: float
    y: float
    z: float
    fiber_rotation: float
    chip_rotation: float
    timestamp: float
    units: str = "um"
    is_homed: bool = False

@dataclass
class MoveCommand:
    """
    Multi-axis movement command with options
    """
    axes: Dict[AxisType, float]  # axis -> target position/distance
    velocity: Optional[float] = None
    coordinated_motion: bool = False  # Move all axes simultaneously
    relative: bool = False  # True for relative moves, False for absolute

@dataclass
class StageConfiguration():
    """
    Configuration parameters for the stage, this will later be altered to be passed through the GUI
    """
    # Communication settings
    com_port: str = '/dev/ttyUSB0'
    baudrate: int = 38400
    timeout: float = 0.3
    
    # Motion parameters (per axis)
    velocities: Dict[AxisType, float] = field(default_factory=lambda: {
        AxisType.X: 2000.0, # From zero xyz
        AxisType.Y: 2000.0,
        AxisType.Z: 2000.0,
        AxisType.ROTATION_FIBER: 100.0,
        AxisType.ROTATION_CHIP: 100.0
    })
    
    accelerations: Dict[AxisType, float] = field(default_factory=lambda: {
        AxisType.X: 100.0, # No Idea
        AxisType.Y: 100.0,
        AxisType.Z: 100.0,
        AxisType.ROTATION_FIBER: 500.0,
        AxisType.ROTATION_CHIP: 500.0
    })
    
    position_limits: Dict[AxisType, Tuple[float, float]] = field(default_factory=lambda: {
        AxisType.X: (-24940.0, 20000.0), # From zero_xyz
        AxisType.Y: (-30400.0, 20000.0),
        AxisType.Z: (-11100.0, 20000.0),
        AxisType.ROTATION_FIBER: (-180.0, 180.0),
        AxisType.ROTATION_CHIP: (-180.0, 180.0)
    })

    # Completion detection settings
    position_tolerance: float = 1.0  # um
    status_poll_interval: float = 0.05  # seconds
    move_timeout: float = 30.0  # seconds

    # # Intial position settings
    # init_pos = {

    # }
    # x_pos: float # start pt in um PLACEHOLDER 
    # y_pos: float # um
    # z_pos: float # um
    # chip_angle: float 
    # fiber_angle: float = 8.0 # degrees

    # factory config ? 
    driver_types: Dict[AxisType, str] = field(default_factory=lambda: {
        AxisType.X: "stage_control", 
        AxisType.Y: "stage_control",
        AxisType.Z: "stage_control",
        AxisType.ROTATION_FIBER: "stage_control",
        AxisType.ROTATION_CHIP: "stage_control"
    })



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
                print(f"[{event.axis.name}] Error in manager‐level callback: {e}")

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
    
    # async def initialize(self, axes):
    #     """
    #     Initialize all stage axes
    #     """
    #     # Succesful initialization
    #     results = {}

    #     for axis in axes:
    #         # Retrive config
    #         cfg = self.config
    #         motor = StageControl(
    #             axis=axis,
    #             com_port=cfg.com_port,
    #             baudrate=cfg.baudrate,
    #             timeout=cfg.timeout,
    #             velocity=cfg.velocities[axis],
    #             acceleration=cfg.accelerations[axis],
    #             position_limits=cfg.position_limits[axis],
    #             position_tolerance=cfg.position_tolerance,
    #             status_poll_interval=cfg.status_poll_interval
    #         )

    #         # Catch exceptions
    #         ok = await self._safe_execute(f"connect {axis.name}", motor.connect()) # motor connects from abstracted stage driver
    #         if ok:
    #             self.motors[axis] = motor
    #             self._last_positions[axis] = 0.0
    #             motor.add_event_callback(self._handle_stage_event)
    #         results[axis] = ok
    #     return all(results.values())

    @requires_motor
    async def home_axis(self, axis: AxisType, direction: int = 0) -> bool:
        ok = await self._safe_execute(f"home {axis.name}", self.motors[axis].home(direction))
       
        # # Wait for home to complete
        # while self.motors[axis]._move_in_progress:
        #     await asyncio.sleep(0.1)
        
        if ok:
            self._last_positions[axis] = 0.0
        return ok
    
    @requires_motor
    async def home_limits(self, axis: AxisType) -> bool:
        ok = await self._safe_execute(f"home {axis.name} limits", self.motors[axis].home_limits())
        if ok:
            self.config.position_limits[axis] = ok
        return ok

    @requires_motor
    async def wait_for_home_completion(self, axis: AxisType) -> bool:
        ok = await self._safe_execute(f"home {axis.name} status", self.motors[axis]._wait_for_home_completion())
        return ok
    
    async def load_params(self) -> bool:
        """
        Loads preset params of a stage
        """
        # # Check if homed
        # for motor in self.motors:
        #     if motor._is_homed:
        #         pass
        #     else:
        #         logger.error(f"Please home all axis")
        #         return False

        # Intialize params
        # cfg = self.config
        # x = self.motors[AxisType.X]
        # y = self.motors[AxisType.Y]
        # z = self.motors[AxisType.Z]
        # fr = self.motors[AxisType.ROTATION_FIBER]
        # cp = self.motors[AxisType.ROTATION_CHIP]
        # all = [x,y,z,fr,cp]

        # # Load params
        # for axis in all:
        #     task_x = asyncio.create_task(axis, )
        
    
    @requires_motor
    async def move_single_axis(self, axis: AxisType, position: float,
                               relative=False, velocity=None,
                               wait_for_completion=True) -> bool:
        """
        Move a single axis command. 

        Args:
            axis[AxisType]: axis you want to move eg. AxisType.X (or something nice like x_axis = AxisType.X)
            position[Float]: Desired position for absolute or relative distance (+/-) 
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

    async def move_xy(self, xy_distance: Tuple[float, float]):
        """
        MMC Supports multi-axes movement. Move only xy in tandem for safety. Relative movement
        
        Args:
            xy_distance: (x,y) Distance you want to move in microns 
        """
        # Need xy to be initialized
        if (AxisType.X not in self.motors) or (AxisType.Y not in self.motors):
            logger.error(f"Axis XY not initialized")
            return False
        
        # Scale
        x_um, y_um = xy_distance
        x_mm = x_um / 1000
        y_mm = y_um / 1000 

        # Cmd for sync relative mvmt
        x_cmd = f"1MSR{x_mm:.6f}"
        y_cmd = f"2MSR{y_mm:.6f}"
        cmd = f"{x_cmd};{y_cmd}"
        
        return await self._safe_execute(f"moving {xy_distance} synchronously", self.motors[AxisType.X].move_xy(cmd))
    @requires_motor
    async def stop_axis(self, axis):
        return await self._safe_execute(f"stop {axis.name}", self.motors[axis].stop())

    async def stop_all_axes(self):
        return {axis: await self.stop_axis(axis) for axis in self.motors}

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
    async def get_state(self, axis) -> Optional[MotorState]:
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
