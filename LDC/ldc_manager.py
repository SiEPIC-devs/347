import asyncio
from typing import Dict, Any
from LDC.hal.ldc_hal import LdcHAL
from LDC.hal.ldc_factory import create_driver


class SRSManager:
    """
    Async manager for SRS LDC instruments, exposing full HAL operations.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        config format:
        {
            "instruments": {
                "name1": {"driver_key": "srs_ldc", "params": {...}},
                ...
            }
        }
        """
        self._cfg = config.get("instruments", {})
        self._instruments: Dict[str, LdcHAL] = {}

    async def initialize_all(self) -> bool:
        """
        Instantiate, open, and configure all instruments.
        Returns True if all succeeded.
        """
        for name, info in self._cfg.items():
            driver = create_driver(info["driver_key"], **info.get("params", {}))
            self._instruments[name] = driver

        # Open and configure in parallel
        results = await asyncio.gather(
            *[asyncio.to_thread(dev.open) for dev in self._instruments.values()],
            *[asyncio.to_thread(dev.configure) for dev in self._instruments.values()],
            return_exceptions=True
        )
        return all(isinstance(r, bool) and r for r in results)

    async def measure_all(self) -> Dict[str, Any]:
        """
        Measure all instruments; returns dict of name -> measurement.
        """
        tasks = {name: asyncio.to_thread(dev.measure) for name, dev in self._instruments.items()}
        readings = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return {
            name: (val if not isinstance(val, Exception) else None)
            for name, val in zip(tasks.keys(), readings)
        }

    async def shutdown_all(self) -> None:
        """
        Safely turn off and close all instruments.
        """
        await asyncio.gather(
            *[asyncio.to_thread(dev.close) for dev in self._instruments.values()],
            return_exceptions=True
        )

    # Temperature control methods
    async def set_temperature(self, name: str, setpoint: float) -> bool:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.set_temperature, setpoint)

    async def get_temperature(self, name: str) -> float:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.get_temperature)

    async def set_heater_on(self, name: str, enable: bool) -> bool:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.set_heater_on, enable)

    async def get_heater_on(self, name: str) -> bool:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.get_heater_on)

    # Laser diode control methods
    async def set_ld_current(self, name: str, current: float) -> bool:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.set_ld_current, current)

    async def get_ld_current(self, name: str) -> float:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.get_ld_current)

    async def set_ld_on(self, name: str, enable: bool) -> bool:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.set_ld_on, enable)

    async def get_ld_on(self, name: str) -> bool:
        dev = self._instruments[name]
        return await asyncio.to_thread(dev.get_ld_on)
