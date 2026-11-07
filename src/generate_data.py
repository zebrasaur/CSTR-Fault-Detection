from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from cstr import simulate
import random
from faults import FaultType, FaultEvent
DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)
"""
Generates disjoint Train, val, and Test datasets for CSTR fault detection.
- Train: Normal runs only (baseline dynamic modeling / residual fitting)
- Val:   Normal runs only (decision threshold & persistence calibration)
- Test:  Disjoint Normal runs (unbiased FAR) + Faulted runs (TDR & detection delay)
"""



@dataclass
class DatasetConfig:
    n_train: int = 20                                              #normal runs
    n_val: int = 20                                                #validation runs
    n_test_normal: int = 50                                        #normal test runs
    n_test_faulted: int = 50                                       #faulted test runs
    base_seed: int = 0                                             #offset += base_seed
    sim_time: float = 1440*14                                      #minutes
    dt: float = 0.05                                               #minutes
    is_faulted: bool = False
    fault_type: str = "none"
    fouling_range: Tuple[float, float] = (0.10, 0.50)              # 10% to 50% loss in UA
    pump_trip_range: Tuple[float, float] = (0.10, 0.70)            # 10% to 70% flow reduction
    sensor_bias_temp_range: Tuple[float, float] = (0.5, 5.0)       # +/- 0.5 K to +5 K measurement bias
    fault_start_window: Tuple[float, float] = (4320.0, 10080.0)    # Start between 3-7 days (minutes)


@dataclass
class RunMetadata:
    run_id: str
    split: str
    fault_start_time: float
    fault_severity: float
    seed: int


def generate_splits(config: DatasetConfig):
    """
    Produces disjoint splits ensuring seed isolation and strict separation
    between normal operational variation and test-only faults.
    """
    manifest: Dict[str, List[Path]] = {
        "train": [],
        "val": [],
        "test": [],
    }

    # Every run receives a strictly non-overlapping integer seed
    seed_offset = config.base_seed
    frames = {"train": [], "val": [], "test": []}
    truth_frames = {"train": [], "val": [], "test": []}
    run_rows = []

    plan = [("train", "none", config.n_train), ("val", "none", config.n_val), ("test", "none", config.n_test_normal),
        ("test", FaultType.FOULING, config.n_test_faulted), ("test", FaultType.PUMP_TRIP, config.n_test_faulted),
        ("test", FaultType.SENSOR_BIAS_TEMP, config.n_test_faulted)]    
    
    rng = np.random.default_rng(config.base_seed)

    for split_name, kind, count in plan:        

        for i in range(count):
            run_id = f"{split_name}_{i:04d}"
            current_seed = seed_offset
            seed_offset += 1

            if kind == "none":
                faults, onset, severity = [], np.nan, 0.0
            else:
                # Randomize fault onset and severity as before
                t_min, t_max = sorted(config.fault_start_window)
                onset = float(rng.uniform(t_min, t_max))
                if   kind == FaultType.FOULING:
                    severity = float(rng.uniform(*sorted(config.fouling_range)))
                elif kind == FaultType.PUMP_TRIP:
                    severity = float(rng.uniform(*sorted(config.pump_trip_range)))
                elif kind == FaultType.SENSOR_BIAS_TEMP:
                    sign = rng.choice([-1.0, 1.0])        # exa
                    severity = float(sign*(rng.uniform(*sorted(config.sensor_bias_temp_range))))
                else:
                    severity = 0.0
                ramp = 3 * 1440.0 if kind == FaultType.FOULING else 0.0
                faults = [FaultEvent(fault_type=kind, t_start=onset, severity=severity, ramp_duration=ramp)]

            
            # Generate trajectory
            sim_data = simulate(duration=config.sim_time, seed=current_seed, faults=faults)
            
            #Extinction Guard
            T_SET = 400.0
            if kind == "none":
                max_dev = np.abs(sim_data["T_true"] - T_SET).max()
            else:
                before = sim_data["time"] < onset                   # True for each sample before the fault starts
                max_dev = np.abs(sim_data["T_true"][before] - T_SET).max()
            
            label = "none" if kind == "none" else kind.value        # plain text fault for the CSV
            sim_data = {k: v[::40] for k, v in sim_data.items()}    # 2-minute logging: every 40th sample of 0.05 min
            df = pd.DataFrame(sim_data)                             # one column per key, one row per sample
            df.insert(0, "run_id", current_seed)                    # seeds never repeat across splits, so run_ids are unique
            df["fault_kind"] = label                                # a single value fills every row
            df["severity"] = severity                               # 0.0 for normal runs
            df["onset"] = onset                                     # np.nan for normal runs
            
            MEASURED = ["run_id", "time", "fault_kind", "severity", "onset","T", "Tc", "Ca", "qc", "qc_cmd", "T0", "Tc_in", "Ca0"]
            TRUTH = ["run_id", "time"] + [c for c in df.columns if c.endswith("_true")]
            frames[split_name].append(df[MEASURED])
            truth_frames[split_name].append(df[TRUTH])
            run_rows.append({"run_id": current_seed, "split": split_name, "fault_kind": label,
                 "severity": severity, "onset": onset,"max_dev": max_dev})

    for split in frames:                                              # "train", then "val", then "test"
        pd.concat(frames[split], ignore_index=True).to_csv(
            DATA / f"{split}.csv", index=False, float_format="%.4f")
        pd.concat(truth_frames[split], ignore_index=True).to_csv(
            DATA / f"{split}_truth.csv", index=False, float_format="%.4f")
    pd.DataFrame(run_rows).to_csv(DATA / "runs.csv", index=False, float_format="%.6f")

if __name__ == "__main__":
    
    dataset_config = DatasetConfig(
        n_train=20,                             # 20 training runs (diminishing returns after 20)
        n_val=20,                               # 20 validation runs (diminishing returns after 20)
        n_test_normal=50,                       # 50 tests with no faults
        n_test_faulted=50,                      # 50 tests of each fault (fouling, pump_trip, sensor_bias_temp)
        base_seed=0,
        sim_time=1440 * 14,                     # minutes
        dt=0.05,                                # minutes
        is_faulted=False,
        fault_type= "none",                     # fouling, pump_trip, sensor_bias_temp
        fouling_range=(0.10, 0.50),             # 10% - 50% conductance loss
        pump_trip_range=(0.10, 0.70),           # 10% - 70% loss
        sensor_bias_temp_range=(0.5, 5.0),      # (K)
        fault_start_window=(4320.0, 10080.0))   # minutes

    splits = generate_splits(dataset_config)











