import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import replace
import threading
from concurrent.futures import ThreadPoolExecutor

from motors_hal import MotorHAL, AxisType, MotorState, Position, MotorConfig, MotorEventType
import serial

"""
Made by: Cameron Basara, 5/30/2025

Prototype implementation of Stage control at 347 using more modern Python features and the motor hardward abstraction layer
"""

class StageControl(MotorHAL):
    """
    
    """
    # Axis Mapping
    AXIS_MAP = {
            AxisType.X: 1,
            AxisType.Y: 2,
            AxisType.Z: 3,
            AxisType.ROTATION_FIBER: 4,
            AxisType.ROTATION_CHIP: 5,
            AxisType.ALL: 0
            }
    
    def __init__(self, axis : AxisType, com_port: str = '/dev/ttyUSB0', 
                 baudrate: int = 38400, timeout: float = 0.3):
        
        super().__init__(axis)
        
        # Serial config 
        self.com_port = com_port
        self.baudrate = baudrate
        self.timeout = timeout

        # Thread pool for blocking operations
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # Serial connection (shared across all axes)
        self._serial_lock = threading.Lock()
        self._serial_port = None
        self._is_connected = False
        
        # Configuration ( arb defaults rn)
        # self._configuration = {

        # }
        self._velocity = 1000.0  # um/s default
        self._acceleration = 5000.0  # um/s^2 default
        self._position_limits = (-50000.0, 50000.0)  # um
        self._step_size = {
            'step_size_x': 1,
            'step_size_y': 1,
            'step_size_z': 1,
            'step_size_fr': 0.1,
            'step_size_cr': 0.1
        } 
        
        # State tracking
        self._last_position = 0.0 # (0.0 , 0.0, 0.0) 
        self._is_homed = False
    
    async def connect(self) -> bool:
        """ 
        Built to match the SiEPIC code base setup, more simple approach
        
        Initialize connection to the serial port
        """
        def _connect(self):
            try:
                if not self._serial_port:
                    self._serial_port = serial.Serial(
                            port=self.com_port,
                            baudrate=self.baudrate,
                            timeout=self.timeout
                        )
                
                if not self._serial_port._is_open:
                    self._serial_port.open()

                # Init axis
                self._send_command(f"{self.AXIS_MAP[self.axis]}SM3")  # Closed loop mode
                time.sleep(0.1)
                self._send_command(f"{self.AXIS_MAP[self.axis]}VA{self._velocity * 0.001}")  # Set velocity
                time.sleep(0.1)

                # Connection successful
                self._is_connected = True 
                return True
            
            except Exception as e:
                print(f"Connection unsuccessful {e}")
                return False
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _connect)
    
    async def disconnect(self):
        """
        Clean up resources, SiEPIC Stage compatible
        """
        if self._serial_port and self._serial_port.is_open:
            self._serial_port.close()
        self._executor.shutdown(wait=True) 
    
    def _send_command(self, cmd : str) -> str:
        """
        Send a command to the motor drivers via serial, opt receive response
        """
        while self._serial_lock():
            if not self._serial_port or not self._serial_port.is_open:
                raise ConnectionError("Serial port not connected")

            self._serial_port.write((cmd + "\r\n").encode('ascii'))
            time.sleep(0.05)  # Small delay for command processing
            
            # Read response if available
            response = ""
            if self._serial_port.in_waiting > 0:
                response = self._serial_port.read_until(b'\r\n').decode('ascii').strip()
                
            return response
        
    def _query_command(self, cmd : str) -> str:
        """
        Send query command and wait for response
        """
        with self._serial_lock:
            if not self._serial_port or not self._serial_port.is_open:
                raise ConnectionError("Serial port not connected")
                
            self._serial_port.write((cmd + "\r\n").encode('ascii'))
            response = self._serial_port.read_until(b'\r\n').decode('ascii')
            return response.strip('#').strip('\r\n')

    # MOVEMENT
    async def move_absolute(self, position, velocity=None):
        """
        Move to absolute position in microns
        """
        def _move():
            try:
                if velocity:
                    # self._send_command(f"{self.AXIS_MAP[self.axis]}VA{velocity:.6f}")
                    pass

                # Convert um to mm
                position_mm = position * 0.001
                self._send_command(f"{self.AXIS_MAP[self.axis]}MVA{position_mm:.6f}") # mmc100 driver format for abs

                # Event handling
                self._emit_event(MotorEventType.MOVE_STARTED, {
                    'target_position': position,
                    'velocity': velocity or self._velocity
                })

                return True 
            
            except Exception as e:
                self._emit_event(MotorEventType.ERROR_OCCURRED, {'error': str(e)})
                return False
        return await asyncio.get_event_loop().run_in_executor(self._executor, _move)
    
    async def move_relative(self, distance, velocity = None):
        """
        Move to rel pos in microns
        """
        def _move_rel(self):
            try:
                if velocity:
                    # self._send_command(f"{self.AXIS_MAP[self.axis]}VA{velocity:.6f}")
                    pass

                # Convert um to mm
                distance_mm = distance * 0.001
                self._send_command(f"{self.AXIS_MAP[self.axis]}MVR{distance_mm:.6f}") # mmc driver format for relmvm

                # Event handling
                self._emit_event(MotorEventType.MOVE_STARTED, {
                    "target_position": self._last_position + distance, # todo 
                    "velocity": velocity or self._velocity
                })

                return True
                    
            except Exception as e:
                self._emit_event(MotorEventType.ERROR_OCCURRED, {'error': str(e)})
                return False
        return await asyncio.get_event_loop().run_in_executor(self._executer, _move_rel)
    
    async def stop(self) -> bool:
        """
        Stop motor motion
        """
        def _stop():
            try:
                self._send_command(f"{self.AXIS_MAP[self.axis]}STP")
                return True
            except Exception as e:
                print(f"Stop error: {e}")
                return False
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _stop)

    async def emergency_stop(self) -> bool:
        """
        Emergency stop all axes
        """
        def _estop():
            try:
                self._send_command("EST")  # Stop all axes
                return True
            except Exception as e:
                print(f"Emergency stop error: {e}")
                return False
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _estop)
        
    # Status and Position
    async def get_position(self):
        """
        Get current position
        """
        def _get_pos():
            try:
                response = self._query_command(f"{self.AXIS_MAP[self.axis]}POS?")
                
                # Parse response: "position,encoder_position"
                parts = response.split(',')
                theoretical_mm = float(parts[0])
                actual_mm = float(parts[0])  # Use same for now
                
                # Convert mm to um
                theoretical_um = theoretical_mm * 1000
                actual_um = actual_mm * 1000
                
                return Position(
                    theoretical=theoretical_um,
                    actual=actual_um,
                    units="um",
                    timestamp=time.time()
                )
                
            except Exception as e:
                print(f"Position read error: {e}")
                return Position(0.0, 0.0, "um", time.time())
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_pos)

    async def get_state(self):
        """
        Get current motor state
        """
        def _get_state():
            try:
                response = self._query_command(f"{self.AXIS_MAP[self.axis]}STA?")
                status_int = int(response)
                
                # Check bit 3 (moving[0]/stopped[1])
                if (status_int >> 3) & 1:
                    return MotorState.IDLE
                else:
                    return MotorState.MOVING
                    
            except Exception as e:
                print(f"State read error: {e}")
                return MotorState.ERROR
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_state)

    async def is_moving(self):
        """
        Check if motor is moving
        """
        state = await self.get_state()
        return state == MotorState.MOVING
    
    # Configuration
    async def set_velocity(self, velocity):
        """
        Set velocity in um/s
        """
        def _set_vel():
            try:
                # Convert um/s to mm/s for controller
                vel_mm_s = velocity * 0.001
                self._send_command(f"{self.AXIS_MAP[self.axis]}VEL{vel_mm_s:.6f}")
                self._velocity = velocity
                return True
            
            except Exception as e:
                print(f"Set velocity error: {e}")
                return False
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _set_vel)
    
    async def set_acceleration(self, acceleration):
        """
        Set acceleration in um/s2
        """
        def _set_acc():
            try:
                # Convert um/s2 to mm/s2 for controller
                acc_mm_s2 = acceleration * 0.001
                self._send_command(f"{self.AXIS_MAP[self.axis]}ACC{acc_mm_s2:.6f}")
                self._acceleration = acceleration
                return True
            
            except Exception as e:
                print(f"Set acceleration error: {e}")
                return False
        return await asyncio.get_event_loop().run_in_executor(self._executor, _set_acc)
    
    async def get_config(self):
        """
        Get motor configuration
        """
        units = "degrees" if self.axis in [AxisType.ROTATION_FIBER, AxisType.ROTATION_CHIP] else "um"
        
        return MotorConfig (
            max_velocity=self._velocity,
            max_acceleration=self._acceleration,
            position_limits=self._position_limits,
            units=units,
            **self._step_size
        )
    
    # Home and limits
    async def home(self, direction= 0):
        """
        Home the axis
        """
        def _home():
            try:
                self._emit_event(MotorEventType.MOVE_STARTED, {'operation': 'homing'})
                
                if direction == 0:
                    self._send_command(f"{self.AXIS_MAP[self.axis]}MLN")  # Move to negative limit
                else:
                    self._send_command(f"{self.AXIS_MAP[self.axis]}MLP")  # Move to positive limit
                
                # Wait for completion
                while True:
                    response = self._query_command(f"{self.AXIS_MAP[self.axis]}STA?")
                    status = int(response)
                    if (status >> 3) & 1:  # Stopped
                        break
                    time.sleep(0.1)
                
                # Set zero point
                self._send_command(f"{self.AXIS_MAP[self.axis]}ZRO")
                self._is_homed = True # todo: check if homed is for specific axis, check super config may be fine

                self._emit_event(MotorEventType.HOMED, {'direction': direction})
                return True
                
            except Exception as e:
                self._emit_event(MotorEventType.ERROR_OCCURRED, {'error': str(e)})
                return False
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _home)

    async def set_zero(self):
        """Set current position as zero"""
        def _set_zero():
            try:
                self._send_command(f"{self.AXIS_MAP[self.axis]}ZRO")
                return True
            except Exception as e:
                print(f"Set zero error: {e}")
                return False
                
        return await asyncio.get_event_loop().run_in_executor(self._executor, _set_zero)