import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import time

from motors_hal import AxisType, MotorState, Position, MotorEvent, MotorEventType
from modern_stage import StageControl

"""
Made by: Cameron Basara, 5/30/2025
(PROTOTYPE)
Stage manager, intended to interface with the GUI to give high level commands to the modern stage

With debug logging
"""

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

logger = logging.getLogger(__name__)

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
class StageConfiguration:
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


class StageManager:
    def __init__(self, config: StageConfiguration):
        self.config = config
        self.motors: Dict[AxisType, StageControl] = {}
        self._callbacks: List[Callable[[MotorEvent], None]] = []
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
            return await coro
        except Exception as e:
            logger.error(f"Error {desc}: {e}")
            logger.debug("Traceback:", exc_info=True)
            return default

    async def initialize(self, axes):
        """
        Initialize all stage axes
        """
        # Succesful initialization
        results = {}

        for axis in axes:
            # Retrive config
            cfg = self.config
            motor = StageControl(
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

            # Catch exceptions
            ok = await self._safe_execute(f"connect {axis.name}", motor.connect()) # motor connects from abstracted stage driver
            if ok:
                self.motors[axis] = motor
                self._last_positions[axis] = 0.0
                motor.add_event_callback(self._on_event)
            results[axis] = ok
        return all(results.values())

    def _on_event(self, event: MotorEvent):
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                logger.exception("Error in event callback")

    @requires_motor
    async def home_axis(self, axis: AxisType, direction: int = 0) -> bool:
        ok = await self._safe_execute(f"home {axis.name}", self.motors[axis].home(direction))
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
    async def move_single_axis(self, axis: AxisType, pos: float,
                               relative=False, velocity=None,
                               wait_for_completion=True) -> bool:
        """
        Move a single axis command. 

        Args:
            axis[AxisType]: axis you want to move eg. AxisType.X (or something nice like x_axis = AxisType.X)
            pos[Float]: Desired position for absolute or relative distance (+/-) 
            relative[bool]: False by default, set true if you want to send a relative movement command
            velocity: Optional velocity override, useless right now
            wait_for_completion: If True, wait for move to complete and emit MOVE_COMPLETED event

        Returns:
            Position if successful else False  
        """
        if relative:
            ok = await self._safe_execute(f"move_relative {axis.name}", 
                    self.motors[axis].move_relative(pos, velocity, wait_for_completion)) 
            if ok:
                self._last_positions[axis] += pos
        else:
            ok = await self._safe_execute(f"move_absolute {axis.name}",
                    self.motors[axis].move_absolute(pos, velocity, wait_for_completion))
            if ok:
                self._last_positions[axis] = pos
        return ok

    # async def move_multiple_axes(self, cmd):
    #     results = {}
    #     tasks = []
    #     for axis, target in cmd.axes.items():
    #         if axis not in self.motors:
    #             results[axis] = False
    #             continue
    #         coro = self.move_single_axis(axis, target, cmd.relative, cmd.velocity, True)
    #         if cmd.coordinated_motion:
    #             tasks.append((axis, asyncio.create_task(coro)))
    #         else:
    #             results[axis] = await coro

    #     if cmd.coordinated_motion:
    #         for axis, task in tasks:
    #             results[axis] = await self._safe_execute(f"coordinated {axis.name}", task)
    #     return results

    @requires_motor
    async def stop_axis(self, axis):
        return await self._safe_execute(f"stop {axis.name}", self.motors[axis].stop())

    async def stop_all_axes(self):
        return {axis: await self.stop_axis(axis) for axis in self.motors}

    async def emergency_stop(self):
        if not self.motors:
            return False
        motor = next(iter(self.motors.values()))
        return await self._safe_execute("emergency_stop", motor.emergency_stop())

    @requires_motor
    async def get_position(self, axis) -> Optional[Position]:
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

    async def disconnect(self, axis: AxisType):
        """
        Disconnect a single motor

        Args:
            axis[AxisType]: axis you wish to disconnect
        """
        await self._safe_execute("disconnect", axis.disconnect())
        del self.motors[axis]
        del self._last_positions[axis]
