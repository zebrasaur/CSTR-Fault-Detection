import numpy as np


#STANDARDIZE (z-scores) IN NUMPY

def standardize_np(data):
    M = np.asarray(data, dtype=np.float64)
    mean = np.mean(M)
    sample_std = np.std(M, ddof=1) #ddof =1 computes std using N-1
    return (M - mean) / sample_std

    #example data
raw_data = [ 10.0, 15.0, 23.0, 42.0]
z_scores = standardize_np(raw_data)
print("Standardized:", np.round(z_scores, 2))


#MOVING AVERAGE IN NUMPY

def moving_average_np(data,window_size):
    N = np.asarray(data, dtype=np.float64)
    
    #kernel of uniform weights [1/w,1/w,...,]
    weights = np.ones(window_size, dtype=np.float64) / window_size
    
    #mode = valid returns values where the window completely overlaps the data
    return np.convolve(N, weights, mode='valid')

    #example
series = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
print("Moving Average (w=3):", moving_average_np(series, window_size=3))


#COUNT CONSECUTIVE IN NUMPY

def count_consecutive_above_np(data,threshold,n) -> bool:
    
    if n <= 0:          #count trivial Case
        return True
    P = np.asarray(data, dtype=np.float64)  
    if P.size < n:       #data size trivial case
        return False
    
    #step 1 : vectorize boolean mask converted to 1s and 0s
    mask = (P > threshold).astype(np.int32)
    
    #step 2 : sum over sliding windows of size n via convolution
    consecutive_counts = np.convolve(mask, np.ones(n, dtype=np.int32), mode='valid')
    
    #step 3 : check if any window reached the target count n
    return bool(np.any(consecutive_counts >= n))

#Example Run
readings = np.array([12.0, 15.5, 18.2, 19.0, 14.1, 21.0])
print("Consecutive exceedance (n=3, thresh=15.0):", 
      count_consecutive_above_np(readings, 15.0, 3))



#RK4 IN NUMPY

def rk4_step_np(f, y: np.ndarray, t, h) -> np.ndarray:
# comutes a single RK4 step for vector state y

    k1 = f(y,t)
    k2 = f(y + 0.5 * h * k1, t + 0.5 * h)
    k3 = f(y + 0.5 * h * k2, t + 0.5 * h)
    k4 = f(y + h * k3, t + h)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


#Generic ODE solver

def solve_ode_rk4_np(f, y0: np.ndarray, t_span: tuple[float,float], h: float):
    #integrates an ODE across t_span using pre-allocated Numpy trajectory
    t0, t_max = t_span
    #create a discrete time grid
    t_points = np.arange(t0, t_max+h/2.0, h)
    num_steps = len(t_points)
    
    #Ensure state vectroer is a float64 numpy array
    y_current = np.asarray(y0, dtype=np.float64)
    state_dim = y_current.shape[0]
    
    #pre-allocate full trajectory array in RAM
    y_trajectory = np.empty((num_steps, state_dim), dtype=np.float64)
    y_trajectory[0] = y_current
    
    for i in range(num_steps -1):
        t_curr = t_points[i]
        step_h = t_points[i + 1] - t_curr
        y_current = rk4_step_np(f, y_current, t_curr, step_h)
        y_trajectory[i + 1] = y_current
        
    return t_points, y_trajectory



#HARMONIC OSCILLATPOR - dy/dt = [v, -omega^2*x]

omega_sq = 4.0

def harmonic_derivs(y, t):
    return np.array([y[1], -omega_sq * y[0]])

#Test example
#solve for x(0) = 1.0, v(0) = 0.0 over 10 seconds

t_grid, states = solve_ode_rk4_np(harmonic_derivs, y0 = [1.0, 0.0], t_span = (0.0, 10.0), h = 0.05)

print(f"Time grid shape:       {t_grid.shape}")       # (201,)
print(f"Trajectory grid shape: {states.shape}")       # (201, 2)
print(f"Final state at t=10.0: x = {states[-1, 0]:.4f}, v = {states[-1, 1]:.4f}")