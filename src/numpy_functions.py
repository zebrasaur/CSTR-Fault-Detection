import numpy as np

#test shapes
v = np.array([10.0, 20.0, 30.0, 40.0])
print(v.shape)

m = np.array([
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12]
])
print(m.shape)


#standardized (z-scores)
def standardize_np(data):
    M = np.asarray(data, dtype=np.float64)
    mean = np.mean(M)
    sample_std = np.std(M, ddof=1)
    return (M - mean) / sample_std

#example data
raw_data = [ 10.0, 15.0, 23.0, 42.0]
z_scores = standardize_np(raw_data)
print("Standardized:", np.round(z_scores, 2))


#moving avrages

def moving_average_np(data,window_size)
    N = np.asarray(data, dtype=np.float64)
    weights = np.ones(window, dtype=np.float64) / window_size
    return np.convolve(N, weights, mode='valid')