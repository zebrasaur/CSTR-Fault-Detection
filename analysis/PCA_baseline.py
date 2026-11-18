import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import numpy as np
import pandas as pd 
from monitoring import evaluate_run, fit_pca, t2_q, alarms
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent

df_train = pd.read_csv(ROOT / "data" / "train.csv")
df_val = pd.read_csv(ROOT / "data" / "val.csv")
tag_whitelist = ["T", "Tc", "Ca", "qc", "T0", "Ca0", "Tc_in", "qc_cmd"]
run_alarm_summary = []
model = fit_pca(df_train[tag_whitelist], k = 5 )
lamdas = model["all_eigenvalues"]   # all eigenvalues

#print lamda table
for i, lam in enumerate(lamdas, start=1):
    print(f"PC{i}: lamda = {lam:.4f} ({lam / 8.0 * 100: .1f}%)")


T2_val, Q_val = t2_q(df_val[tag_whitelist], model)
alpha_stat = (1/720) / 2       #overall divided by 2 sources(T2,Q)

T2_lim = float(np.quantile(T2_val, 1.0 - alpha_stat))
Q_lim = float(np.quantile(Q_val, 1.0 - alpha_stat))

for run_id, run_df in df_val.groupby("run_id", sort=False):
    T2_run, Q_run = t2_q(run_df[tag_whitelist], model)
    
    latched_T2 = alarms(T2_run, threshold=T2_lim, persistence=4)
    latched_Q = alarms(Q_run, threshold=Q_lim, persistence=4)
    latched = latched_T2 | latched_Q #1-D boolean array of length n_samples
    
    did_alarm = bool(latched.any())  #single True/False scalar for the run
    run_alarm_summary.append({
            "run_id": run_id,
            "alarm_triggered": did_alarm,
            "first_alarm_index": int(np.argmax(latched)) if did_alarm else None})

summary_df = pd.DataFrame(run_alarm_summary)
out = ROOT / "results" / "PCA_test.csv"
out.parent.mkdir(parents=True, exist_ok=True)
summary_df.to_csv(out, index=False)

print(f"Total Runs: {len(summary_df)}")
print(f"Runs with False Alarms: {summary_df['alarm_triggered'].sum()}")





