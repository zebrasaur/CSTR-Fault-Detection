import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import numpy as np
import pandas as pd 
from monitoring import evaluate_run
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


windows = range(2, 8)  # w = 2, 3, 4, 5, 6, 7

df_all = pd.read_csv("data/val.csv")
tag_whitelist = ["T", "Tc", "Ca", "qc", "T0", "Ca0", "Tc_in", "qc_cmd"]


baseline_stats = {}
for tag in tag_whitelist:
        mu = float(df_all[tag].mean())
        sigma = float(df_all[tag].std(ddof=1))
        baseline_stats[tag] = (mu, sigma)
    
#Set the Bonferroni critical threshold
#720 samples/day, 8 tags, 2 tailed test
alpha_overall = 1.0 / 720.0                         #one False Alarm per day
alpha_tail = alpha_overall / (2.0 * len(tag_whitelist)) #m = 8
threshold = float(stats.norm.ppf(1.0 - alpha_tail)) #Zcrit = 3.7546

evaluate_runs = []
run_alarm_summary = []

for w in windows:
    for run_id, run_df in df_all.groupby("run_id", sort=False):

        latched = evaluate_run(run_df=run_df,
                           tag_whitelist=tag_whitelist,
                           baseline_stats=baseline_stats,
                           threshold=threshold,
                           persistence=w)
    
        did_alarm = bool(latched.any())
        run_alarm_summary.append({
            "run_id": run_id,
            "alarm_triggered": did_alarm,
            "window" : w,
            "first_alarm_index": int(np.argmax(latched)) if did_alarm else None})

summary_df = pd.DataFrame(run_alarm_summary)
out = ROOT / "results" / "sensitivity.csv"
out.parent.mkdir(parents=True, exist_ok=True)
summary_df.to_csv(out, index=False)

print(f"Total Runs: {len(summary_df)}")
print(f"Runs with False Alarms: {summary_df['alarm_triggered'].sum()}")

