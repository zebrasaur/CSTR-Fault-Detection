"""
Generates disjoint Train, Validation, and Test datasets for CSTR fault detection.
- Train: Normal runs only (baseline dynamic modeling / residual fitting)
- Val:   Normal runs only (decision threshold & persistence calibration)
- Test:  Disjoint Normal runs (unbiased FAR) + Faulted runs (TDR & detection delay)
"""

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from cstr import simulate
import random


class FaultType(str, Enum):
    NONE = "none"
    FOULING = "fouling"       # Drop in heat transfer coefficient (UA)
    PUMP_TRIP = "pump_trip"   # Sudden loss or drop in coolant flow capacity
    SENSOR_BIAS_TEMP = "sensor_bias_temp"     # Step bias added to reactor temperature sensor
    
@dataclass(frozen=True)
class FaultSeverityRanges:
    """Continuous boundaries [min, max] for randomized fault severities."""
    sign = random.choice([-1, 1])
    fouling: Tuple[float, float] = (0.10, 0.50)         # 10% to 50% loss in UA
    pump_trip: Tuple[float, float] = (0.10, 0.70)       # 10% to 70% flow reduction
    sensor_bias_temp: Tuple[float, float] = sign*(0.5, 5.0) # +/- 0.5 K to +5 K measurement bias


@dataclass
class DatasetConfig:
    n_train: int = 20
    n_val: int = 20
    n_test_normal: int = 50
    n_test_faulted: int = 50
    base_seed: int = 0
    sim_time: float = 1440          #minutes
    dt: float = 0.05                #minutes
    fault_start_window: Tuple[float, float] = (120.0, 420.0)  # Start between 2 hr and 7 hr
    severity_ranges: FaultSeverityRanges = field(default_factory=FaultSeverityRanges)


@dataclass
class RunMetadata:
    run_id: str
    split: str
    is_faulted: bool
    fault_type: str
    fault_start_time: float
    fault_severity: float
    seed: int


def get_severity(fault_type, config: DatasetConfig):
    
    rng = np.random.Generator
    t_start = rng.uniform(*config.fault_start_window)

    ranges = config.severity_ranges
    if fault_type == FaultType.FOULING:
        severity = rng.uniform(*ranges.fouling)
    elif fault_type == FaultType.PUMP_TRIP:
        severity = rng.uniform(*ranges.pump_trip)
    elif fault_type == FaultType.SENSOR_BIAS_TEMP:
        severity = rng.uniform(*ranges.sensor_bias_temp)
    else:
        raise ValueError(f"severity zero")

    return t_start, severity
    



def generate_splits(config: DatasetConfig, output_dir: Path):
    """
    Produces disjoint splits ensuring seed isolation and strict separation
    between normal operational variation and test-only faults.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, List[Path]] = {
        "train": [],
        "validation": [],
        "test_normal": [],
        "test_faulted": [],
    }

    # Deterministic global seed counters
    # Every run receives a strictly non-overlapping integer seed
    seed_offset = config.base_seed

    plan = [
        ("train", config.n_train, False),
        ("validation", config.n_val, False),
        ("test_normal", config.n_test_normal, False),
        ("test_faulted", config.n_test_faulted, True),
    ]

    for split_name, count, is_faulted in plan:
        split_dir = output_dir / split_name
        split_dir.mkdir(exist_ok=True)

        for i in range(count):
            run_id = f"{split_name}_{i:04d}"
            current_seed = seed_offset
            seed_offset += 1
            run_rng = np.random.default_rng(current_seed)

            if is_faulted:
                f_type, f_start, f_sev = sample_fault_parameters(run_rng, config)
            else:
                f_type, f_start, f_sev = FaultType.NONE, None, 0.0

            meta = RunMetadata(
                run_id=run_id,
                split=split_name,
                is_faulted=is_faulted,
                fault_type=f_type.value,
                fault_start_time=f_start,
                fault_severity=round(f_sev, 4),
                seed=current_seed,
            )

            # Generate trajectory
            sim_data = simulate(duration = 1440.0)

            # Persist array payload and discrete metadata
            run_file = split_dir / f"{run_id}.npz"
            np.savez_compressed(
                run_file,
                **sim_data,
                metadata_json=json.dumps(meta.__dict__)
            )
            manifest[split_name].append(run_file)

    # Export generation manifest
    summary_path = output_dir / "split_manifest.json"
    with open(summary_path, "w") as f:
        json.dump(
            {
                "config": config.__dict__,
                "counts": {k: len(v) for k, v in manifest.items()},
                "severity_ranges": config.severity_ranges.__dict__,
            },
            f,
            indent=2,
            default=str
        )

    return manifest


if __name__ == "__main__":
    dataset_config = DatasetConfig(
        n_train=1,
        n_val=1,
        n_test_normal=1,
        n_test_faulted=0,
        base_seed=0,
        sim_time = 1440.0,
        dt = 0.05,
        fault_start_window=(120.0, 420.0),
    )

    out_path = Path("./data/runs")
    splits = generate_splits(dataset_config, out_path)

    print(f"Generated {len(splits['train'])} Train runs (NOC)")
    print(f"Generated {len(splits['validation'])} Validation runs (NOC - threshold tuning)")
    print(f"Generated {len(splits['test_normal'])} Test-Normal runs (held-out FAR)")
    print(f"Generated {len(splits['test_faulted'])} Test-Faulted runs (TDR & detection delay)")










