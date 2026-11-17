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


def fit_pca(x_train, k):
    '''X is (n_samples, n_tags) of NORMAL data. Standardize internally.
    Return a model (dict or object) exposing at least:
    mean, std, loadings (n_tags, n_components), eigenvalues'''

    arr = np.asarray(x_train, dtype = np.float64)
    
    #Fit SVD & standardization on POOLED training data
    mu = np.mean(arr, axis=0)
    sigma = np.std(arr, axis=0, ddof=1)
    z_train = (arr - mu) / sigma
    U, S, Vt = np.linalg.svd(z_train, full_matrices=False)
    P = Vt.T        # shape (8,8) (8 tags x 8 componentss) columns are the 8 principle directions (eingvectors)
    
    T_all = z_train @ P
    z_hat_all = T_all @ P.T
    residual = z_train - z_hat_all
    max_error = np.max(np.abs(residual))
    assert max_error < 1e-12, f"Full-rannk reconstruction failed, Residual = {max_error}"
    
    n_train = z_train.shape[0]
    lamdas = (S ** 2) / (n_train - 1)
    #sanity check lamdas
    if not np.isclose(np.sum(lamdas), arr.shape[1]):
        raise ValueError(f"Not standardized correctly: sum of lamdas = {np.sum(lamdas)}")   
    
    
    P_k = P[:, :k]          #shape (8,k), loadings
    lamdas_k = lamdas[:k]   #shape (k), eigenvalues
    
    return {
        "mean": mu,
        "std": sigma,
        "loadings": P[:, :k],
        "eigenvalues": lamdas[:k],
        "all_eigenvalues": lamdas, 
    }
    
def t2_q(x_val, model):
    '''Return (T2, Q), each of length n_samples.'''  
    arr = np.asarray(x_val, dtype=np.float64)   
    mean = model["mean"]                # shape: (n_features,)
    std = model["std"]          # shape: (n_features,)
    P_k = model["loadings"]              # shape: (n_features, k)
    lamdas_k = model["eigenvalues"]  # shape: (k,)    
    z_stat = (arr - mean) / std
    scores = z_stat @ P_k
    
    T2 = np.sum((scores ** 2) / lamdas_k, axis=1)
    z_hat = scores @ P_k.T 
    residual = z_stat - z_hat
    Q = np.sum(residual ** 2, axis=1)

    return T2, Q
    
    
    
    
