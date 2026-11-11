import numpy as np 
import pandas as pd
from scipy import stats

def alarms(stat: np.ndarray, threshold: float, persistence: int):
    """ 
    Boolean array, true from the first latched alarm onwards.
    An alarm latches after persistence consecutive exceedances.
    """
    
    arr = np.asarray(stat, dtype = np.float64)
    n = len(arr)
    latched = np.zeros(n, dtype = bool)

    if n == 0:
        return latched
    # If persistence requirement is <= 0, Error message
    if persistence <= 0:
        raise ValueError(f"Persistence can not be zero or negative")
    
    current_streak = 0
    
    for i, val in enumerate(arr):
        if val > threshold:
            current_streak += 1
            if current_streak >= persistence:
                latched[i:] = True
                break
        else:
            #reset counter
            current_streak = 0
    
    return latched


def compute_stat(x: np.ndarray, mu: float, sigma: float):
    """
    Computes per-sample absolute standardized score (|Z|) using validation parameters.
    
    Parameters:
        x: 1D array of tag values for a single run.
        mu: Mean of the tag fitted on validation data.
        sigma: Sample standard deviation (ddof=1) fitted on validation data.
    """
    
    arr = np.asarray(x, dtype = np.float64)
    if sigma <= 0.0:
        raise ValueError(f"sigma must be positive")
        
    #standardize using validation baseline parameters
    
    z_scores = np.abs(arr - mu) / sigma
    
    return z_scores    

def evaluate_run(run_df: pd.DataFrame, tag_whitelist: list[str],
                 baseline_stats: dict[str, tuple[float, float]],
                 threshold: float,
                 persistence: int = 3):
    """ 
    Runs alarm detection on a single run_id:
    - Independent same-tag persistence per tag.
    - Any tag breaking latches the whole sample.
    - Output length matches len(run_df) with no index offset.
    """
    n_samples = len(run_df)
    run_alarm_latched = np.zeros(n_samples, dtype=bool)
    
    for tag in tag_whitelist:
        mu, sigma = baseline_stats[tag]
        raw_x = run_df[tag].to_numpy()
        
    #step 1: per sample |z| (exact length n, no NaNs)
    stat = compute_stat(raw_x, mu, sigma)
    #step 2: Same-tag persistence check and latching
    tag_latched = alarms(stat, threshold=threshold, persistence=persistence)
    #step 3: if any tag breaks, the whole sample trips
    run_alarm_latched = run_alarm_latched | tag_latched
    
    return run_alarm_latched


df_all = pd.read_csv("data/train.csv")
tag_whitelist = ["T", "Tc", "Ca", "qc", "T0", "Ca0", "Tc_in", "qc_cmd"]

#Compute baseline stats across all 20 treaining runs. Mean and sample
#Standard deviation are fitted on the entire clean dataset
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
persistence = 3

evaluate_runs = []
run_alarm_summary = []

for run_id, run_df in df_all.groupby("run_id", sort=False):
    #Slice is passed independently: streak counter strictly starts at 0
    latched = evaluate_run(run_df=run_df,
                           tag_whitelist=tag_whitelist,
                           baseline_stats=baseline_stats,
                           threshold=threshold,
                           persistence=persistence)
    run_result = run_df.copy()
    run_result["is_alarm_latched"] = latched
    evaluate_runs.append(run_result)
    
    did_alarm = bool(latched.any())
    run_alarm_summary.append({
        "run_id": run_id,
        "alarm_triggered": did_alarm,
        "first_alarm_index": int(np.argmax(latched)) if did_alarm else None
    })
    
df_final = pd.concat(evaluate_runs, ignore_index=True)
summary_df = pd.DataFrame(run_alarm_summary)

print(f"Total Runs: {len(summary_df)}")
print(f"Runs with False Alarms: {summary_df['alarm_triggered'].sum()}")



""" TESTS START HERE
    
# 1. Length preservation check
data = np.array([100.0, 102.0, 105.0, 98.0, 104.0])
stat = compute_stat(data, mu=100.0, sigma=2.0)
assert len(stat) == len(data)
assert not np.isnan(stat).any()

# 2. 2-in-a-row does NOT trip a 3-sample rule
# Thr = 3.0, P = 3. Two breaches, then drops, then three breaches
stat = np.array([1.0, 3.5, 4.0, 1.2, 3.2, 3.8, 4.1, 0.5])
out = alarms(stat, threshold=3.0, persistence=3)

# Indices 1, 2 exceed (streak = 2) -> should NOT trip
assert not out[1] and not out[2] and not out[3]

# Indices 4, 5, 6 exceed (streak reaches 3 at index 6) -> Latch occurs
assert not out[4] and not out[5]
assert out[6] and out[7]  # Remains latched until end of run
print("✓ All assertions passed: strict index alignment, no NaNs, and exact latching.")
print(f"stat = {stat}, out = {out}")

"""
