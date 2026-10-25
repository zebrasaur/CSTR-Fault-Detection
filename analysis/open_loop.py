import numpy as np 
import matplotlib.pyplot as plt
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

if __name__ == "__main__":
    
    h = 0.25                          #time step or dt in minutes 
    t_range = (0.0, 200.0)            #simulate for 200 minutes
    C_A, T, Tc, mc, X_A = solve_steady_state(400.0,p)  #ss values
    y_initial = [C_A, T, Tc]         #initial state vector
    y_b = [C_A, T + 2.0, Tc]         #b case T
    y_c = [C_A, T -10.0, Tc]         #c case T
    y_d = [600, 390, 345]            #d case non steady state initial


    time, states_initial = solve_cstr_dynamic(y_initial, t_range, h, mc)
    time, states_b = solve_cstr_dynamic(y_b, t_range, h, mc)
    time, states_c = solve_cstr_dynamic(y_c, t_range, h, mc)
    time, states_d = solve_cstr_dynamic(y_d, t_range, h, mc)


    print(f"Time Grid Shape:                {time.shape}")
    print(f"delta t:                        {h}")
    print(f"Final Concentration ss:         {states_initial[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp ss:          {states_initial[-1, 1]:.5f} K")
    print(f"Final Jacket Temp ss:           {states_initial[-1, 2]:.5f} K")
    print(f"Final Concentration b case:    {states_b[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp b case:     {states_b[-1, 1]:.5f} K")
    print(f"Final Jacket Temp b case:      {states_b[-1, 2]:.5f} K")
    print(f"Final Concentration c case:    {states_c[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp c case:     {states_c[-1, 1]:.5f} K")
    print(f"Final Jacket Temp c case:      {states_c[-1, 2]:.5f} K")
    print(f"Final Concentration d case:    {states_d[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp d case:     {states_d[-1, 1]:.5f} K")
    print(f"Final Jacket Temp d case:      {states_d[-1, 2]:.5f} K")

    fig, (ax1) = plt.subplots(figsize=(9, 6))

    # Subplot 1: Thermal Convergence
    ax1.plot(
        time,
        states_initial[:, 1],
        "r-",
        linewidth=2,
        label="Steady State Reactor Temperature $T(t)$",
    )
    ax1.plot(
        time,
        states_b[:, 1],
        "b--",
        linewidth=1.8,
        label="Case b Reactor Temperature $T(t)$",
    )
    ax1.plot(
        time,
        states_c[:, 1],
        "g:",
        linewidth=1.5,
        label="Case c Reactor Temperature $T(t)$",
    )
    ax1.plot(
        time,
        states_d[:, 1],
        "m+",
        linewidth=1.8,
        label="Case d Reactor Temperature $T(t)$",
    )
    ax1.set_title("CSTR Dynamic Trajectory Simulation (RK4)", fontweight="bold")
    ax1.set_ylabel("Temperature (K)", fontsize=11)
    ax1.set_xlabel("Time (min)", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(Path(__file__).resolve().parent.parent / "figures" / "Dynamic_property_plots.png", dpi=150)
    plt.show()       
