import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
runs = pd.read_csv(DATA / "runs.csv")
test = pd.read_csv(DATA / "test.csv")
truth = pd.read_csv(DATA / "test_truth.csv")

print(runs.to_string(), "\n")
print("measured and truth rows match:", len(test) == len(truth))
print("logging step (min):", test.groupby("run_id")["time"].diff().dropna().unique())
print("missing values in measured tags:",
      test[["T", "Tc", "Ca", "qc", "qc_cmd", "T0", "Tc_in", "Ca0"]].isna().sum().sum(), "\n")

for rid, g in test.groupby("run_id"):
    tr = truth[truth["run_id"] == rid]
    print(f"run {rid}: {g['fault_kind'].iloc[0]:17s} severity {g['severity'].iloc[0]:+.3f}  "
          f"onset day {g['onset'].iloc[0] / 1440:.2f}  "
          f"UA_true {tr['UA_true'].iloc[0]:.0f} -> {tr['UA_true'].iloc[-1]:.0f}  "
          f"T_true end {tr['T_true'].iloc[-1]:.2f}  T end {g['T'].iloc[-1]:.2f}  "
          f"qc_cmd end {g['qc_cmd'].iloc[-1]:.1f}")
