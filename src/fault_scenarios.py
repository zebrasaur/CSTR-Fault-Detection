import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from faults import FaultType, FaultEvent
 

# Scenario A: Partial Coolant Pump Failure (70% flow loss at t = 10 min)

pump_failure_test = [
    FaultEvent(
        fault_type=FaultType.PUMP_TRIP,
        t_start= 10.0,                               # minutes
        severity= 0.70,                              # leaves only 30% available flow
    )
]


# Scenario B: Progressive Exchanger Fouling (30% loss ramped over 15 min)

heat_exchanger_fouling_test = [
    FaultEvent(
        fault_type=FaultType.FOULING,
        t_start= 5.0,
        severity= 0.30,                              # 30% drop in UA
        ramp_duration= 15.0,                         #ramps down between t=5 and t=20 min
    )
]

# Scenario C: Severe Compound Stress Test (Concentration spike + Sensor Bias)
compound_test = [
    FaultEvent(
        fault_type=FaultType.FEED_CONC_SURGE,
        t_start= 5.0,
        t_end= 20.0,                                #transient shock that clears after 8 min
        severity= 400.0,                            #+400 mol/m3 (+16% reactant)
    ),
    FaultEvent(
        fault_type=FaultType.SENSOR_BIAS,
        t_start= 12.0,
        severity= -5.0,                            #RTD reports 5 K colder than reality
    ),
]
