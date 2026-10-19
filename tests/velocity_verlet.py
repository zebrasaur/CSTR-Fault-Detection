import numpy as np

# System parameters (identical to your previous runs)
m = 1.0
k_spring = 4.0
omega_sq = k_spring / m

def acceleration(x):
    return -omega_sq * x

def compute_energy(x, v):
    return 0.5 * m * (v ** 2) + 0.5 * k_spring * (x ** 2)

# Simulation configuration
h = 0.05
t_max = 10.0
t_points = np.arange(0.0, t_max + h / 2.0, h)
num_steps = len(t_points)

# State initialization
x = 1.0
v = 0.0
a = acceleration(x)
E0 = compute_energy(x, v)

print(f"{'Time (t)':>8} | {'Position (x)':>13} | {'Velocity (v)':>13} | {'Energy (E)':>12} | {'Verlet Drift':>15} | {'RK4 Drift (from run)':>22}")
print("-" * 92)

for i, t in enumerate(t_points):
    current_energy = compute_energy(x, v)
    drift = current_energy - E0
    
    # Print every 1.0 second
    if np.isclose(t % 1.0, 0.0) or np.isclose(t % 1.0, 1.0):
        # Comparison with the RK4 values you logged earlier
        rk4_drifts = {
    0.0: 0.0,
    1.0: -5.5486e-7,
    2.0: -1.1097e-6,
    3.0: -1.6646e-6,
    4.0: -2.2194e-6,
    5.0: -2.7743e-6,
    6.0: -3.3292e-6,
    7.0: -3.8840e-6,
    8.0: -4.4389e-6,
    9.0: -4.9937e-6,
    10.0: -5.5486e-6,
}
        rk4_val = rk4_drifts.get(round(t, 1), np.nan)
        print(f"{t:>8.2f} | {x:>13.6f} | {v:>13.6f} | {current_energy:>12.6f} | {drift:>+15.4e} | {rk4_val:>+22.4e}")

    # Velocity Verlet Step
    v_half = v + 0.5 * h * a       # Step 1: half kick
    x = x + h * v_half             # Step 2: full drift
    a = acceleration(x)            # Step 3: compute new force
    v = v_half + 0.5 * h * a       # Step 4: final half kick
