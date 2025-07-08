from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
import json


@dataclass
class LDCConfig:
    """Configuration for one SRS LDC500-series controller."""
    visa_address: str                    # e.g. "GPIB0::10::INSTR"
    sensor_type: str = "TH1"           # temperature sensor channel
    pid_coeffs: List[float] = field(
        default_factory=lambda: [1.0, 0.1, 0.01]
    )                                      # [P, I, D]
    setpoint: float = 25.0               # °C
    ld_current: float = 0.0              # mA, laser diode current
    ld_on: bool = False                  # laser diode output enable


@dataclass
class StageConfiguration:
    """Holds configuration for motors and instruments."""
    # motors: Dict[str, MotorConfig]     # assume existing motor configs handled elsewhere
    instruments: Dict[str, LDCConfig] = field(
        default_factory=lambda: {
            # default instrument entry (override in JSON/YAML)
            "ldc1": LDCConfig(visa_address="GPIB0::10::INSTR"),
        }
    )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "StageConfiguration":
        """Construct StageConfiguration from a dict (e.g. parsed JSON)."""
        instr_data = data.get("instruments", {})
        instruments: Dict[str, LDCConfig] = {}
        for name, cfg in instr_data.items():
            instruments[name] = LDCConfig(
                visa_address=cfg["visa_address"],
                sensor_type=cfg.get("sensor_type", "TH1"),
                pid_coeffs=cfg.get("pid_coeffs", [1.0, 0.1, 0.01]),
                setpoint=cfg.get("setpoint", 25.0),
                ld_current=cfg.get("ld_current", 0.0),
                ld_on=cfg.get("ld_on", False)
            )
        return StageConfiguration(instruments=instruments)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a dict, suitable for JSON/YAML."""
        return {
            # "motors": { ... }  # handled separately
            "instruments": {
                name: asdict(cfg) for name, cfg in self.instruments.items()
            }
        }

    def get_instrument_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Return each instrument’s config as a JSON-safe dict,
        ready to pass to create_driver().
        """
        return {
            name: asdict(cfg)
            for name, cfg in self.instruments.items()
        }

    def save_to_json(self, path: str) -> None:
        """Write configuration to a JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load_from_json(path: str) -> "StageConfiguration":
        """Load configuration from a JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return StageConfiguration.from_dict(data)
