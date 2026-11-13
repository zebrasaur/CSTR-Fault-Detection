import numpy as np 
import pandas as pd

def alarms(stat: np.ndarray, threshold: float, persistence: int):
    """ 
    Boolean array, true from the first latched alarm onwards.
    An alarm latches after persistence consecutive exceedances.
    """
    
    arr = np.asarray(stat, dtype = np.float64)
    n = len(arr)
    latched = np.zeros(n, dtype = bool)
    
    # If persistence requirement is <= 0, Error message
    if persistence <= 0:
        raise ValueError(f"Persistence can not be zero or negative")

    if n == 0:
        return latched
    
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

