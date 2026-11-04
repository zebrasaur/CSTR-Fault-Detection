import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from faults import FaultType, FaultEvent
 
 
@dataclass(frozen=True)
class FaultSeverityRanges:
    """Continuous boundaries [min, max] for randomized fault severities."""
    fouling: Tuple[float, float] = (0.10, 0.50)         # 10% to 50% loss in UA
    pump_trip: Tuple[float, float] = (0.10, 0.70)       # 10% to 70% flow reduction
    sensor_bias_temp: Tuple[float, float] = (-5.0, 5.0) # -5 K to +5 K measurement bias
 
 
def fault_parameters(rng: np.random.Generator, config: DatasetConfig):
    """Randomly select fault type, start time, and severity within bounds."""
    
    candidate_faults = [
        FaultType.FOULING,
        FaultType.PUMP_TRIP,
        FaultType.SENSOR_BIAS_TEMP,
    ]
    fault_type = rng.choice(candidate_faults)
    t_start = rng.uniform(*config.fault_start_window)

    ranges = config.severity_ranges
    if fault_type == FaultType.FOULING:
        severity = rng.uniform(*ranges.fouling)
    elif fault_type == FaultType.PUMP_TRIP:
        severity = rng.uniform(*ranges.pump_trip)
    elif fault_type == FaultType.SENSOR_BIAS_TEMP:
        severity = rng.uniform(*ranges.sensor_bias_temp)
    else:
        severity = 0.0

    return fault_type, float(t_start), float(severity) 
 
 