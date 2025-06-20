import json
import struct
from multiprocessing import shared_memory
from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple, Any
from modern.hal.motors_hal import AxisType

# SHM and json framing consts
MAX_PAYLOAD = 2048
SHM_SIZE = 4 + MAX_PAYLOAD # 4 byte u_int32
_LEN_STRUCT = struct.Struct("<I") # 4 byte u_int32 length header 
SHM_NAME = "stage_config" # fixed shared mem name


@dataclass
class StageConfiguration:
    """Stage config data class to load data to manager"""
    com_port: str = "/dev/ttyUSB0"
    baudrate: int = 38400
    timeout: float = 0.3
    velocities: Dict[AxisType, float] = field(default_factory=lambda:
        {ax:2000.0 for ax in AxisType if ax.name!="ALL"}
    ) # field dict values
    position_limits: Dict[AxisType, Tuple[float,float]] = field(default_factory=lambda:
        {ax:(0.0,10000.0) for ax in AxisType if ax.name!="ALL"}
    ) # field dict values

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts self -> JSON-safe dict, turning any AxisType keys
        into string names.
        """
        d = asdict(self)
        # rewrite the two dicts with string keys
        d["velocities"] = {ax.name: v for ax, v in self.velocities.items()}
        d["position_limits"] = {ax.name: list(lim)
                                 for ax, lim in self.position_limits.items()}
        return d

    # Need to convert to and from JSON from SHM
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageConfiguration":
        """
        Reconstruct from a dict (e.g. JSON-loaded). Converts string
        keys back to AxisType.
        """
        # extract stage config properties
        vel = {AxisType[name]: v for name, v in data["velocities"].items()} 
        lim = {AxisType[name]: tuple(lim)
               for name, lim in data["position_limits"].items()}
        
        return cls(
            com_port=data["com_port"],
            baudrate=data["baudrate"],
            timeout=data["timeout"],
            velocities=vel,
            position_limits=lim
        )
