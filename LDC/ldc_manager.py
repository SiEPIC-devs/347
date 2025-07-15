import asyncio
import logging
from typing import Dict, Any, Callable, List
from LDC.ldc_controller import SrsLdc502
from LDC.hal.ldc_hal import *
from LDC.hal.ldc_factory import create_driver
from LDC.config.ldc_config import *
from LDC.utils.shared_memory import *

"""
Created by Cameron Basara, 7/15/2025

Manager to control the SRS LDC 50x Devices. Currently does not support LD control.
Implemented to work at 347, where only the TEC is in use

TODO:
    Extend usage to work with other stages
    Extend usage to work with LD, and its functionality
    Potential merge of managers
"""

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class SRSManager:
    def __init__(self, profile_config: LDCConfiguration, create_shm: bool = True):
        self._connected: bool = False
        self._event_callbacks: List[Callable[[LDCEvent], None]] = []
        self.ldc = None  # Will hold the LDC controller instance
        
        if create_shm:
            self.shm_config = create_shared_ldc_config()
            write_shared_ldc_config(self.shm_config, profile_config)
        else:
            # If an shm has been created, simply access the open memory block
            self.shm_config = open_shared_ldc_config()
                
        # Read from shm
        self.config = read_shared_ldc_config(self.shm_config)

    # Async helpers
    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Proper async cleanup with context manager exit"""
        await self.cleanup()

    # Helper decorator to ensure SHM is properly cleaned
    async def cleanup(self):
        """Cleanup method for shm"""
        self.disconnect()
        # Cleanup SHM (BUT don't unlink, that is the main process responsibility)
        try:
            # Destroy instances of shared memory access buffers
            if hasattr(self, 'config'):
                del self.config
            if hasattr(self, 'shm_config'):
                self.shm_config.close()
                self.shm_config.unlink()
        except (FileNotFoundError, AttributeError):
            pass  # Cleared mem or never existed
        except Exception as e:
            logger.error(f"Shared memory cleanup error: {e}")

    def initialize(self):
        """
        Initialize all LDC 50x
        """
        # Successful initialization
        result = False
        
        # Retrieve config
        cfg = self.config
        
        # Instantiate motors through the factory
        driver_key = cfg.driver_key
        driver_cls = cfg.driver_cls
        
        params = dict(
            visa_address=cfg.visa_address,
            sensor_type=cfg.sensor_type,
            model_coeffs=cfg.model_coeffs,
            pid_coeffs=cfg.pid_coeffs,
            temp_setpoint=cfg.setpoint,
        )
        
        self.ldc = create_driver(driver_key, **params)
        ok = self.connect()
        if ok:
            self.ldc.add_event_callback(self._handle_stage_event)
            self._connected = True
            
        result = ok
        return result

    # Connection methods
    def connect(self) -> bool:
        """Connect to the LDC device"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized. Call initialize() first.")
                return False
                
            success = self.ldc.connect()
            if success:
                self._connected = True
                logger.info("Successfully connected to LDC device")
            else:
                logger.error("Failed to connect to LDC device")
            return success
            
        except Exception as e:
            logger.error(f"[CONNECT] Caught Exception: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from the LDC device"""
        try:
            if self.ldc:
                success = self.ldc.disconnect()
                if success:
                    self._connected = False
                    logger.info("Successfully disconnected from LDC device")
                return success
            return True
            
        except Exception as e:
            logger.error(f"[DISCONNECT] Caught Exception: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to the LDC device"""
        return self._connected

    # Configuration methods
    def get_config(self) -> Dict[str, Any]:
        """Get configuration parameters"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return {}
                
            return self.ldc.get_config()
            
        except Exception as e:
            logger.error(f"[GET_CONFIG] Caught Exception: {e}")
            return {}

    def set_sensor_type(self, sensor_type: str) -> bool:
        """Configure sensor type for the LDC device"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            success = self.ldc.set_sensor_type(sensor_type)
            if success:
                logger.info(f"Sensor type set to: {sensor_type}")
            else:
                logger.error(f"Failed to set sensor type to: {sensor_type}")
            return success
            
        except Exception as e:
            logger.error(f"[SET_SENSOR_TYPE] Caught Exception: {e}")
            return False

    def configure_sensor_coeffs(self, coeffs: List[float]) -> bool:
        """Set the coefficients for the sensor model"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            if len(coeffs) != 3:
                logger.error("Sensor coefficients must be a list of 3 floats [A, B, C]")
                return False
                
            success = self.ldc.configure_sensor_coeffs(coeffs)
            if success:
                logger.info(f"Sensor coefficients configured: A={coeffs[0]}, B={coeffs[1]}, C={coeffs[2]}")
            else:
                logger.error("Failed to configure sensor coefficients")
            return success
            
        except Exception as e:
            logger.error(f"[CONFIGURE_SENSOR_COEFFS] Caught Exception: {e}")
            return False

    def configure_PID_coeffs(self, coeffs: List[float]) -> bool:
        """Set the coefficients for PID control"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            if len(coeffs) != 3:
                logger.error("PID coefficients must be a list of 3 floats [P, I, D]")
                return False
                
            success = self.ldc.configure_PID_coeffs(coeffs)
            if success:
                logger.info(f"PID coefficients configured: P={coeffs[0]}, I={coeffs[1]}, D={coeffs[2]}")
            else:
                logger.error("Failed to configure PID coefficients")
            return success
            
        except Exception as e:
            logger.error(f"[CONFIGURE_PID_COEFFS] Caught Exception: {e}")
            return False

    # TEC control methods
    def tec_on(self) -> bool:
        """Turn on the TEC"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            success = self.ldc.tec_on()
            if success:
                logger.info("TEC turned on successfully")
            else:
                logger.error("Failed to turn on TEC")
            return success
            
        except Exception as e:
            logger.error(f"[TEC_ON] Caught Exception: {e}")
            return False

    def tec_off(self) -> bool:
        """Turn off the TEC"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            success = self.ldc.tec_off()
            if success:
                logger.info("TEC turned off successfully")
            else:
                logger.error("Failed to turn off TEC")
            return success
            
        except Exception as e:
            logger.error(f"[TEC_OFF] Caught Exception: {e}")
            return False

    def tec_status(self) -> bool:
        """Get TEC status - True if on, False if off"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            status = self.ldc.tec_status()
            logger.info(f"TEC status: {'ON' if status else 'OFF'}")
            return status
            
        except Exception as e:
            logger.error(f"[TEC_STATUS] Caught Exception: {e}")
            return False

    # Temperature control methods
    def get_temp(self) -> float:
        """Get current temperature reading"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return None
                
            temp = self.ldc.get_temp()
            if temp is not None:
                logger.info(f"Current temperature: {temp}°C")
            else:
                logger.error("Failed to read temperature")
            return temp
            
        except Exception as e:
            logger.error(f"[GET_TEMP] Caught Exception: {e}")
            return None

    def set_temp(self, temperature: float) -> bool:
        """Set target temperature"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return False
                
            success = self.ldc.set_temp(temperature)
            if success:
                logger.info(f"Temperature setpoint set to: {temperature}°C")
            else:
                logger.error(f"Failed to set temperature to: {temperature}°C")
            return success
            
        except Exception as e:
            logger.error(f"[SET_TEMP] Caught Exception: {e}")
            return False

    def get_temp_setpoint(self) -> float:
        """Get current temperature setpoint"""
        try:
            if not self.ldc:
                logger.error("LDC not initialized")
                return None
                
            # This would typically be stored in the device or config
            # For now, return the configured setpoint
            return self.config.setpoint
            
        except Exception as e:
            logger.error(f"[GET_TEMP_SETPOINT] Caught Exception: {e}")
            return None

    # Event handling methods
    def add_event_callback(self, callback: Callable[[LDCEvent], None]):
        """Register callback for LDC events."""
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable[[LDCEvent], None]):
        """Remove event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def _handle_stage_event(self, event: LDCEvent) -> None:
        """Internal method to forward LDC event emitted"""
        for cb in self._event_callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.error(f"Error in manager-level callback: {e}")

    # Utility methods
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information and status"""
        try:
            if not self.ldc:
                return {"error": "LDC not initialized"}
                
            return {
                "connected": self._connected,
                "tec_status": self.tec_status(),
                "current_temp": self.get_temp(),
                "temp_setpoint": self.get_temp_setpoint(),
                "visa_address": self.config.visa_address,
                "sensor_type": self.config.sensor_type,
                "model_coeffs": self.config.model_coeffs,
                "pid_coeffs": self.config.pid_coeffs
            }
            
        except Exception as e:
            logger.error(f"[GET_DEVICE_INFO] Caught Exception: {e}")
            return {"error": str(e)}

    # Context manager for safe operations
    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.disconnect()