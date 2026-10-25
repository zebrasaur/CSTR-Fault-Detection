import numpy as np 
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from cstr import default_params, solve_steady_state, derivatives
from integrate import rk4_step

p = default_params()       

def solve_cstr_dynamic(y_initial, t_range, h, mc, p=p):
    #simulates the cstr using a 2D trajectory array
    
    t_start, t_end = t_range        #time in minutes
    t_points = np.arange(t_start, t_end+(h/2.0), h) #time grid in minutes
    num_steps = len(t_points)
    y_curr = np.asarray(y_initial)
    state_dim = y_curr.shape[0]
    trajectory = np.empty((num_steps, state_dim), dtype=np.float64)
    trajectory[0,:] = y_curr
    
    #March time forward
    for i in range(num_steps-1):
        t_curr = t_points[i]
        step_h = t_points[i + 1] - t_curr
        y_curr = rk4_step(derivatives, y_curr, t_curr, step_h, p, mc)
        trajectory[i+1,:] = y_curr
    return t_points, trajectory

h = 0.5                          #time step or dt in minutes 
t_range = (0.0, 200.0)            #simulate for 200 minutes
C_A, T, Tc, mc, X_A = solve_steady_state(400.0,p)  #ss values
y_initial = [C_A, T, Tc]         #initial state vector

time, states = solve_cstr_dynamic(y_initial, t_range, h, mc)


print(f"Time Grid Shape:       {time.shape}")
print(f"2D Trajectory Shape:   {states.shape}")
print(f"Final Concentration:   {states[-1, 0]:.5f} mol/m^3")
print(f"Final Reactor Temp:    {states[-1, 1]:.5f} K")
print(f"Final Jacket Temp:     {states[-1, 2]:.5f} K")
        
