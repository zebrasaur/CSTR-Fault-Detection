import numpy as np 
import matplotlib.pyplot as plt
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from cstr import default_params, solve_steady_state, derivatives
from integrate import rk4_step

p = default_params()       


h = 0.05                          #time step or dt in minutes 
t_range = (0.0, 60.0)            #simulate time in minutes

C_A_ss, Tss, Tc_ss, mc_ss, X_A_ss = solve_steady_state(400.0,p)  #steady state values

y_initial = [C_A_ss, Tss, Tc_ss]         #initial state vector from steady state
y_b = [C_A_ss, Tss + 2.0, Tc_ss]         #b case: Temperature changed
y_c = [C_A_ss, Tss -10.0, Tc_ss]         #c case: Temperature changed
y_d = [C_A_ss, 475.0, Tc_ss]           #d case: (designed start up values)


#step test with mc
mc_step = mc_ss*(1+0.03)

def solve_cstr_dynamic(y_initial, t_range, h, mc_step, p=p):
    '''simulates the cstr without control for controller parameters'''
    
    t_start, t_end = t_range                            #time in minutes
    t_points = np.arange(t_start, t_end+(h/2.0), h)     #time grid in minutes
    num_steps = len(t_points)
    y_curr = np.asarray(y_initial)
    state_dim = y_curr.shape[0]
    trajectory = np.empty((num_steps, state_dim), dtype=np.float64)
    trajectory[0,:] = y_curr

    #Move time forward
    for i in range(num_steps-1):
        t_curr = t_points[i]
        step_h = t_points[i + 1] - t_curr
                
        y_curr = rk4_step(derivatives, y_curr, t_curr, step_h, p, mc_step)  #RK4 step

        trajectory[i+1,:] = y_curr
        
    return t_points, trajectory


#Solve
time, states  = solve_cstr_dynamic(y_initial, t_range, h, mc_step)

T_inital = states[0,1]
T_final = states[-1,1]

delta_T = T_final - T_inital
T_drift = abs(states[-1,1] - states[-int(5/h) -1 ,1])
dmc = mc_step - mc_ss
Kp = delta_T/dmc


#controller parameters
y_traj= states[:, 1]
y_0 = y_traj[0]
y_inf = y_traj[-1]
delta_y = y_inf - y_0
if np.isclose(delta_y, 0.0, atol=1e-5):
        raise ValueError(
            "State trajectory shows no dynamic response (delta_y ~ 0)."
        )
        
y_third = 0.2835                       #smith 2 point fit 1/3
y_full = 0.6321                       #smith 2 point fit 1.0
y_28 = y_0 + y_third*delta_y
y_63 = y_0 + y_full*delta_y

#Continuous interpolation for exact sub-step accuracy
#np.interp requires the x-series to be strictly increasing.

if delta_y < 0:  # Trajectory cools down (y decreases)
        t_28 = float(np.interp(y_28, y_traj[::-1], time[::-1]))
        t_63 = float(np.interp(y_63, y_traj[::-1], time[::-1]))
else:  # Trajectory heats up (y increases)
        t_28 = float(np.interp(y_28, y_traj, time))
        t_63 = float(np.interp(y_63, y_traj, time))

tau_1 = 1.5*(t_63 - t_28)
theta = t_63 - tau_1
tau_c = 1.5*theta
Kc = tau_1 / ( abs(Kp)*(tau_c + theta) )
tau_I =min(tau_1 ,4*(tau_c + theta) )

print(f"mc_step =  {mc_step}")
print(f"T28 =   {y_28}, T63 = {y_63}")
print(f"t_28 =  {t_28}, t_63 = {t_63}")
print(f"tau =   {tau_1}, Kp = {Kp}, theta = {theta}")
print(f"Kc =    {Kc}, tau_I = {tau_I}")
