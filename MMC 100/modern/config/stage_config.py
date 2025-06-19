from multiprocessing import shared_memory
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, Tuple
from modern.hal.motors_hal import AxisType

@dataclass
class StageConfiguration:
    """Stage config data class that only works for 347"""
    com_port: str = "/dev/ttyUSB0"
    baudrate: int = 38400
    timeout: float = 0.3
    velocities: Dict[AxisType, float] = None
    position_limits: Dict[AxisType, Tuple[float,float]] = None

    def __post_init__(self):
        # default maps if none provided
        if self.velocities is None:
            self.velocities = { ax:2000.0 for ax in AxisType if ax!=AxisType.ALL }
        if self.position_limits is None:
            self.position_limits = { ax:(0.0,10000.0) for ax in AxisType if ax!=AxisType.ALL }

    def to_shared_memory(self):
        """Serialize to JSON and copy into a new SHM block."""
        js = json.dumps({
            "com_port": self.com_port,
            "baudrate": self.baudrate,
            "timeout": self.timeout,
            "velocities": {ax.name: v for ax, v in self.velocities.items()},
            "position_limits": {ax.name: lim for ax, lim in self.position_limits.items()},
        }).encode("utf-8")
        shm = shared_memory.SharedMemory(create=True, size=len(js)) # Should contain a name to identify the shared mem block
        shm.buf[:len(js)] = js
        return shm, len(js)

    @classmethod
    def from_shared_memory(cls, name: str, length: int):
        """Attach to SHM, parse JSON, return a new StageConfiguration."""
        shm = shared_memory.SharedMemory(name=name)
        raw = bytes(shm.buf[:length])
        data = json.loads(raw.decode("utf-8"))
        # convert back to AxisType keys
        velocities = {AxisType[ax]: v for ax, v in data["velocities"].items()}
        limits     = {AxisType[ax]: tuple(lim) for ax, lim in data["position_limits"].items()}
        cfg = cls(
            com_port=data["com_port"],
            baudrate=data["baudrate"],
            timeout=data["timeout"],
            velocities=velocities,
            position_limits=limits
        )
        shm.close() # shm.unlink() has no effect on windows systems
        return cfg
    
