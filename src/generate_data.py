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
"""
Generates disjoint Train, val, and Test datasets for CSTR fault detection.
- Train: Normal runs only (baseline dynamic modeling / residual fitting)
- Val:   Normal runs only (decision threshold & persistence calibration)
- Test:  Disjoint Normal runs (unbiased FAR) + Faulted runs (TDR & detection delay)
"""



@dataclass
class DatasetConfig:
    n_train: int = 20
    n_val: int = 20
    n_test_normal: int = 50
    n_test_faulted: int = 50
    base_seed: int = 0
    sim_time: float = 1440*14           #minutes
    dt: float = 0.05                    #minutes
    is_faulted: bool = False
    fault_type: str = "none"
    fouling_range: Tuple[float, float] = (0.10, 0.50)         # 10% to 50% loss in UA
    pump_trip_range: Tuple[float, float] = (0.10, 0.70)       # 10% to 70% flow reduction
    sensor_bias_temp_range: Tuple[float, float] = (0.5, 5.0) # +/- 0.5 K to +5 K measurement bias
    fault_start_window: Tuple[float, float] = (4320.0, 10,080.0)  # Start between 2-7 days (minutes)


@dataclass
class RunMetadata:
    run_id: str
    split: str
    fault_start_time: float
    fault_severity: float
    seed: int


def generate_splits(config: DatasetConfig, output_dir: Path):
    """
    Produces disjoint splits ensuring seed isolation and strict separation
    between normal operational variation and test-only faults.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, List[Path]] = {
        "train": [],
        "val": [],
        "test": [],
    }

    # Deterministic global seed counters
    # Every run receives a strictly non-overlapping integer seed
    seed_offset = config.base_seed

    plan = [
        ("train", config.n_train, False),
        ("val", config.n_val, False),
        ("test", config.n_test_faulted, True),
    ]
    rng = np.random.default_rng(config.base_seed)

    for split_name, count, is_faulted in plan:
        split_dir = output_dir / split_name
        split_dir.mkdir(exist_ok=True)

        for i in range(count):
            run_id = f"{split_name}_{i:04d}"
            current_seed = seed_offset
            seed_offset += 1

            if not is_faulted:
                faults = []
                fault_onset = 0.0
                severity = 0.0
            else:   
                # Randomize fault onset and severity as before
                t_min, t_max = sorted(config.fault_start_window)
                fault_onset = float(rng.uniform(t_min, t_max))

                if fault_type == FaultType.FOULING:
                    severity = float(rng.uniform(*sorted(config.fouling_range)))
                elif fault_type == FaultType.PUMP_TRIP:
                    severity = float(rng.uniform(*sorted(config.pump_trip_range)))
                elif fault_type == FaultType.SENSOR_BIAS_TEMP:
                    severity = float(rng.uniform(*sorted(config.sensor_bias_temp_range)))
                else:
                    severity = 0.0


            fault_obj = FaultEvent(fault_type=FaultType, fault_onset=fault_onset, severity=severity)
            faults = [fault_obj]
            
            # Generate trajectory
            sim_data = simulate(
                duration=config.sim_time,
                seed=current_seed,
                faults=faults,
                severity=severity,
                fault_onset=fault_onset,
            )
            sim_data = {k: v[::40] for k, v in sim_data.items()}  # 2-minute logging: every 40th sample of 0.05 min
            df = pd.DataFrame(sim_data)  # one column per key, one row per sample
            df.insert(0, "run_id", current_seed)                  # seeds never repeat across splits, so run_ids are unique
            df["fault"] = config.fault_type                       # a single value fills every row
            df["severity"] = severity                             # 0.0 for normal runs
            df["onset"] = onset                                   # np.nan for normal runs
            
            MEASURED = ["run_id", "time", "fault_type", "severity", "onset","T", "Tc", "Ca", "qc", "qc_cmd", "T0", "Tc_in", "Ca0"]
            TRUTH = ["run_id", "time"] + [c for c in df.columns if c.endswith("_true")]
            frames, truth_frames, run_rows = [], [], []
            frames.append(df[MEASURED])
            truth_frames.append(df[TRUTH])
            run_rows.append({"run_id": current_seed, "split": "train", "fault": fault_type,
                 "severity": severity, "onset": onset})

    pd.concat(frames, ignore_index=True).to_csv(DATA / "train.csv", index=False, float_format="%.4f")
    pd.concat(truth_frames, ignore_index=True).to_csv(DATA / "train_truth.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    
    dataset_config = DatasetConfig(
        n_train=2,
        n_val=2,
        n_test_normal=2,
        n_test_faulted=0,
        base_seed=0,
        sim_time=1440 * 14,  # minutes
        dt=0.05,             # minutes
        is_faulted=False,
        fault_type= "none",
        fouling_range=(0.10, 0.50),
        pump_trip_range=(0.10, 0.70),
        sensor_bias_temp_range=(0.5, 5.0),
        fault_start_window=(4320.0, 10080.0),

    )

    out_path = Path("./data/runs")
    splits = generate_splits(dataset_config, out_path)











