import numpy as np 
import matplotlib.pyplot as plt
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from cstr import default_params, solve_steady_state, derivatives, solve_cstr_dynamic
from integrate import rk4_step

p = default_params()       

h = 0.05                          #time step or dt in minutes 
t_range = (0.0, 60.0)            #simulate time in minutes

C_A, T, Tc, mc_ss, X_A = solve_steady_state(400.0,p)  #steady state values

y_initial = [C_A, T, Tc]         #initial state vector from steady state
y_b = [C_A, T + 2.0, Tc]         #b case: Temperature changed
y_c = [C_A, T -10.0, Tc]         #c case: Temperature changed
y_d = [C_A, 475.0, Tc]           #d case: (designed start up values)


#step test with mc
mc_step = mc_ss*(1-0.03)

#solve
time, states = solve_cstr_dynamic(y_initial, t_range, h, mc_step)

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

print(
        f"T28 = {y_28}, T63 = {y_63}, "
        f"t_28 = {t_28}, t_63 = {t_63}, "
        f"tau = {tau_1}, Kp = {Kp}, theta = {theta}, "
        f" mc,ss = {mc_ss}"
)
