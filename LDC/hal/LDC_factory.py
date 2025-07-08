from typing import Type, Dict
from LDC.hal.LDC_hal import LDCHAL

_registry: Dict[str, Type[LDCHAL]] = {}

def register_driver(name: str, cls: Type[LDCHAL]) -> None:
    """Call once in each driver module to make it discoverable."""
    _registry[name] = cls

def create_driver(name: str, **params) -> LDCHAL:
    """Instantiate a registered driver 'name'; raises if driver not registered"""
    try:
        driver = _registry[name]
    except KeyError:
        raise ValueError(f"Driver not yet registered named '{name}'")
    return driver(**params)
