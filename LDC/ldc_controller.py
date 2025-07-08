import pyvisa
from LDC.hal.LDC_hal import LDCHAL


class SrsLdcHAL(LDCHAL):
    """HAL for SRS LDC500 series using VISA (GPIB) communication."""

    def __init__(
        self,
        visa_address: str,
        sensor_type: str = "TH1",
        pid_coeffs: list[float] = (1.0, 0.1, 0.01),
        setpoint: float = 25.0,
    ):
        self._visa_addr = visa_address
        self._sensor_type = sensor_type
        self._pid_p, self._pid_i, self._pid_d = pid_coeffs
        self._setpoint = setpoint
        self._rm = pyvisa.ResourceManager()
        self._inst = None

    def open(self) -> bool:
        """Open VISA session and basic instrument init."""
        try:
            self._inst = self._rm.open_resource(self._visa_addr)
            # Set a reasonable timeout
            self._inst.timeout = 5000  # ms
            # Reset instrument to known state
            self._inst.write("*RST")
            return True
        except Exception:
            return False

    def configure(self) -> bool:
        """Apply sensor, PID, and setpoint configurations."""
        if self._inst is None:
            return False
        try:
            # Select temperature sensor
            self._inst.write(f"SENS:TYPE {self._sensor_type}")
            # Configure PID loop parameters
            self._inst.write(f"LOOP:PROPortion {self._pid_p}")
            self._inst.write(f"LOOP:INTeration {self._pid_i}")
            self._inst.write(f"LOOP:DERivation {self._pid_d}")
            # Set temperature setpoint
            self._inst.write(f"SOUR:COOL:TEMP {self._setpoint}")
            # Enable TEC output
            self._inst.write("OUTP ON")
            return True
        except Exception:
            return False

    def measure(self) -> float:
        """Query and return current temperature."""
        resp = self._inst.query("MEAS:TEMP?")
        return float(resp.strip())

    def close(self) -> None:
        """Disable TEC and close VISA session."""
        if self._inst:
            try:
                self._inst.write("OUTP OFF")
            except Exception:
                pass
            self._inst.close()
        self._rm.close()

    # Temperature control overrides
    def set_temperature(self, setpoint: float) -> bool:
        try:
            self._inst.write(f"SOUR:COOL:TEMP {setpoint}")
            self._setpoint = setpoint
            return True
        except Exception:
            return False

    def get_temperature(self) -> float:
        return self.measure()

    def set_heater_on(self, enable: bool) -> bool:
        try:
            cmd = "OUTP ON" if enable else "OUTP OFF"
            self._inst.write(cmd)
            return True
        except Exception:
            return False

    def get_heater_on(self) -> bool:
        resp = self._inst.query("OUTP?")
        return bool(int(resp.strip()))

    # Laser diode control overrides
    def set_ld_current(self, current: float) -> bool:
        try:
            self._inst.write(f"SOUR:LD:CURR {current}")
            return True
        except Exception:
            return False

    def get_ld_current(self) -> float:
        resp = self._inst.query("SOUR:LD:CURR?")
        return float(resp.strip())

    def set_ld_on(self, enable: bool) -> bool:
        try:
            cmd = "OUTP:LD ON" if enable else "OUTP:LD OFF"
            self._inst.write(cmd)
            return True
        except Exception:
            return False

    def get_ld_on(self) -> bool:
        resp = self._inst.query("OUTP:LD?")
        return bool(int(resp.strip()))
