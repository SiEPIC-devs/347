import pyvisa
import logging
from time import sleep
from typing import Dict, Any

from LDC.hal.ldc_hal import LdcHAL
"""
Made by: Cameron Basara, 7/14/2025

LDC 502 controller wrapped by HAL to be used at 347 Stage. Does not support LD controller
"""

"""
try:

except Exception as e:
        logger.error(f"[]Caught Exception: {e}")
        return False

"""

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class SrsLdc502(LdcHAL):
    """Driver for SRS LDC500 series using VISA (GPIB) communication."""

    def __init__(
        self,
        visa_address: str,
        sensor_type: str,
        model_coeffs: list[float],
        pid_coeffs: list[float],
        temp_setpoint: float,
    ):
        super().__init__()
        self._visa_addr = visa_address
        self._sensor_type = sensor_type
        self._pid_p, self._pid_i, self._pid_d = pid_coeffs
        self._model_A, self._model_B, self._model_C = model_coeffs
        self._temp_setpoint = temp_setpoint
        self._rm = pyvisa.ResourceManager() 
        self._inst = None # Opened visa ressource

    def connect(self) -> bool:
        """Open VISA session and basic instrument init."""
        try:
            self._inst = self._rm.open_resource(
                self._visa_addr,
                baud_rate=9600,  # Manual says this doesn't matter, but 9600 is common
                timeout=5000,
                write_termination='\n',  # Commands must be terminated with CR or LF
                read_termination='\n',
            )
            # Connector in 347 has PROLOGIX GPIB-USB controller, params need to be conf
            self._inst.write('++mode 1')
            sleep(0.1)
            self._inst.write(f'++addr {2}')
            sleep(0.1)
            self._inst.write('++auto 1') # auto read responses after sending cmds
            sleep(0.1)
            self._inst.write('++eoi 1') # Enable EOI assertion w last char
            sleep(0.1)
            self._inst.write('++eos 0')  # Set GPIB term CR+LF
            sleep(0.1)
            self._inst.write('++read_tmo_ms 3000') # time out set to 3s
            sleep(0.1)

            self._inst.write('*IDN?')
            resp = self._inst.read() # read IDN query
            print(f"Connected to {resp.strip()}")

            self.connected = True 
            logger.info("Successfully connected to device")
            return True
        
        except Exception as e:
            logger.error(f"Connection error {e}")
            return False
        
    def disconnect(self) -> bool:
        """Disable TEC and close VISA session."""
        try:
            if self._inst:
                try:
                    self._inst.write("TEON 0") # only power off TEC for this Stage
                except Exception:
                    pass
                self._inst.close()
            self._rm.close()
            self.connected = False
            logger.info("Successfully disconnected to TEC and Powered off")
            return True
        except Exception as e:
            logger.error(f"Error on disconnect {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get configuration parameters"""
        try:
            return {
                'visa_address': self._visa_addr,
                'sensor_type': self._sensor_type,
                'pid_coeffs': [self._pid_p, self._pid_i, self._pid_d],
                'model_coeffs': [self._model_A, self._model_B, self._model_C],
                'setpoint': self._temp_setpoint,
                'connected': getattr(self, 'connected', False),
                'driver_type': 'srs_ldc_502'
            }
        except Exception as e:
            logger.error(f"[GET_CONFIG] Caught Exception: {e}")
            return {}
    
    # TEC controller
    def tec_on(self) -> bool:
        """Turn on TEC"""
        try:
            self._inst.write("TEON 1")
            sleep(0.1)
            if self.tec_status():
                logger.info("TEC on")
                return True
            else:
                logger.warning("TEC on failed")
                return False
        except Exception as e:
            logger.error(f"[TEC_ON] Caught Exception: {e}")
            return False

    def tec_off(self) -> bool:
        """Turn off TEC"""
        try:
            self._inst.write("TEON 0")
            sleep(0.1)
            if not self.tec_status():
                logger.info("TEC off")
                return True
            else:
                logger.warning("TEC off failed")
                return False
        except Exception as e:
            logger.error(f"[TEC_OFF] Caught Exception: {e}")
            return False

    def tec_status(self) -> bool:
        """Return TEC status, True if on False if off"""
        try:
            self._inst.write("TEON?")
            sleep(0.1)
            resp = self._inst.read()
            
            if resp.strip() == "1":
                return True
            elif resp.strip() == "0":
                return False
            else:
                raise Exception("Unknown TEC response")
        except Exception as e:
            logger.error(f"[TEC_STATUS] Caught Exception: {e}")
            return False

    def get_temp(self) -> float:
        """Get current temperature"""
        try:
            self._inst.write("TTRD?")
            sleep(0.1)
            resp = self._inst.read()
            resp = float(resp.strip())
            logger.info(f"Got temp: {resp}")
            return resp
        except Exception as e:
            logger.error(f"[GET_TEMP] Caught Exception: {e}")
            return None
   
    def set_temp(self, temperature: float) -> bool:
        """Set desired temperature"""
        try:
            # Check temp lims at stage
            if temperature > 75.0 or temperature < 15.0:
                raise Exception("Temperature surpases limits (15-75) C")
            
            self._inst.write(f"TEMP {temperature}")
            sleep(0.1)
            t = self.get_temp()
            logger.info(f"Temp set: {t}")
            return True
        except Exception as e:
                logger.error(f"[SET_TEMP] Caught Exception: {e}")
                return False
   
    def set_sensor_type(self, sensor_type: str) -> bool:
        """Configure for sensor models on LDC 50x devices"""
        try:
            self._inst.write(f"TMDN {sensor_type}") # no return available
            return True
        except Exception as e:
                logger.error(f"[SET_SENSOR_TYPE] Caught Exception: {e}")
                return False
    
    def configure_sensor_coeffs(self, coeffs: list[float]) -> bool:
        """Set the coefficients for whichever sensor model is configured"""
        try:
            # Write for MODEL A,B,C specific to stage
            self._inst.write(f"TSHA {str(coeffs[0])}")
            sleep(0.2)
            self._inst.write(f"TSHB {str(coeffs[1])}")
            sleep(0.2)
            self._inst.write(f"TSHC {str(coeffs[2])}")
            sleep(0.2)
            return True
        except Exception as e:
                logger.error(f"[CONF_SENSOR_COEFFS] Caught Exception: {e}")
                return False

    def configure_PID_coeffs(self, coeffs: list[float]) -> bool:
        """Set the coefficients for PID control"""
        try:
            # Write for P,I,D specific to stage
            self._inst.write(f"TPGN {str(coeffs[0])}")
            sleep(0.2)
            self._inst.write(f"TIGN {str(coeffs[1])}")
            sleep(0.2)
            self._inst.write(f"TDGN {str(coeffs[2])}")
            sleep(0.2)
            return True
        except Exception as e:
                logger.error(f"[CONF_PID] Caught Exception: {e}")
                return False
     
     # LD controller

    def ldc_on(self) -> bool:
        """Turn LDC on"""
        pass
    
    def ldc_off(self) -> bool:
        """Turn LDC off"""
        pass
    
    def ldc_state(self) -> str:
        """Check state of LDC"""
        pass
    
    def set_voltage_limit(self, limit: float) -> bool:
        """Set voltage limit"""
        pass
    
    def get_voltage_limit(self) -> float:
        """Get voltage limit"""
        pass
    
    def set_current_limit(self, limit: float) -> bool:
        """Set current limit"""
        pass
    
    def get_current_limit(self) -> float:
        """Get current limit"""
        pass
    
    def set_current(self, current: float) -> bool:
        """Configure current setpoints"""
        pass
    
    def get_current(self) -> float:
        """Read current"""
        pass
    
    def get_voltage(self) -> float:
        """Read voltage"""
        pass
    
    def set_current_range(self, toggle: int) -> bool:
        """Set range to be either High or Low"""
        pass


from LDC.hal.ldc_factory import register_driver
register_driver("srs_ldc_502", SrsLdc502)