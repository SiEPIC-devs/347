from abc import ABC, abstractmethod
from typing import Any


class LDCHAL(ABC):
    """Abstract base class for hardware abstraction layers of LDC devices."""

    @abstractmethod
    def open(self) -> bool:
        """Establish connection and perform any initial handshake or setup."""
        pass

    @abstractmethod
    def configure(self) -> bool:
        """Apply configuration parameters (e.g., setpoints, gains)."""
        pass

    @abstractmethod
    def measure(self) -> Any:
        """Take a measurement or reading (e.g., temperature, signal)."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Safely shut down and close the connection."""
        pass

    # Temperature control interface
    def set_temperature(self, setpoint: float) -> bool:
        """Set the temperature setpoint. Override if supported."""
        raise NotImplementedError("Temperature control not supported.")

    def get_temperature(self) -> float:
        """Get the current measured temperature. Override if supported."""
        raise NotImplementedError("Temperature reading not supported.")

    def set_heater_on(self, enable: bool) -> bool:
        """Enable or disable the heating element (TEC). Override if supported."""
        raise NotImplementedError("Heater on/off not supported.")

    def get_heater_on(self) -> bool:
        """Return the heater (TEC) on state. Override if supported."""
        raise NotImplementedError("Heater on/off query not supported.")

    # Laser-diode control interface
    def set_ld_current(self, current: float) -> bool:
        """Set the laser diode drive current. Override if supported."""
        raise NotImplementedError("Laser diode current control not supported.")

    def get_ld_current(self) -> float:
        """Get the current laser diode drive current. Override if supported."""
        raise NotImplementedError("Laser diode current reading not supported.")

    def set_ld_on(self, enable: bool) -> bool:
        """Enable or disable the laser diode. Override if supported."""
        raise NotImplementedError("Laser diode on/off not supported.")

    def get_ld_on(self) -> bool:
        """Return the laser diode on/off state. Override if supported."""
        raise NotImplementedError("Laser diode on/off query not supported.")
