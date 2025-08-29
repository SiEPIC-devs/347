from dataclasses import dataclass, field
from typing import List

"""
Fine Align Configuration
Cameron Basara, 2025
"""

@dataclass
class FineAlignConfiguration:
    step_size = 0.1  # microns
    scan_window = 10 # microns
    threshold = -10.0 # not used
    min_gradient_ss = 0.2 # microns 
    max_gradient_iters = 10 # step size decreases
    primary_detector = None # None sets lowest loss, ch1->1.1;ch2->1.2   
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'step_size': self.step_size,
            'scan_window': self.scan_window,
            'threshold': self.threshold,
            'max_gradient_iters': self.max_gradient_iters,
            'min_gradient_ss': self.min_gradient_ss,
            'primary_detector': self.primary_detector
        }
    
    @classmethod
    def default(cls) -> 'FineAlignConfiguration':
        """Create default configuration"""
        return cls()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FineAlignConfiguration':
        """Create from dictionary"""
        return cls(**data)