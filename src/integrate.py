import numpy as np
from RK4_integrate import rk4_step


def test_ode(y,t):
    return -0.5 * y

def exact_solution(t, y0):
    return y0 * np.exp(-0.5 * t)


# Helper function to capture numeric inputs with fallback defaults
def ask_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} (Press Enter for {default}): ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"Invalid number entered. Falling back to default: {default}")
        return default

def print_table(h, y0, t_max):
    times, values = array_ode(h, y0, t_max)
    exact = exact_solution(times, y0)
    errors = np.abs(values- exact)
    print(f"\n{'Time (t)':>10} | {'RK4 (y)':>12} | {'Exact (y)':>12} | {'Abs Error':>12}")
    print("-" * 55)

    for t, y, e, err in zip(times, values, exact, errors):
        print(f"{t:>10.4f} | {y:>12.4f} | {e:>12.4f} | {err:>12.4e}")

# Prompt the user for parameters

def prompt_and_run():
    print("=== RK4 ODE Solver Configuration ===")
    h = ask_float("Step size (h)", default=0.1)
    y0 = ask_float("Initial state (y0)", default=100.0)
    t_max = ask_float("Total simulation time (t_max)", default=1.0)
    print_table(h, y0, t_max)
    

#initialize state
def array_ode(h, y0, t_max):
    
    """ Return (times, values) as numpy arrays."""
    y = np.array([y0])
    t = 0.0
    times = [t]
    values = [y[0]]
    
   # Advance time using RK4 until t_max is reached
    while t < (t_max - 1e-9):
        
        current_h = min(h, t_max - t)
        y = rk4_step(test_ode, y, t, current_h)
        t += current_h
        
        #append t values and y values into new list
        times.append(t)
        values.append(y[0])   
    
    return np.array(times), np.array(values)

def max_error(h, y0=100.0, t_max=1.0):
    
    times, values = array_ode(h, y0, t_max)
    return np.abs(values - exact_solution(times, y0)).max()
    
def check_convergence():
    
    e1, e2 = max_error(0.1), max_error(0.05)
    ratio = e1/e2
    assert 8 < ratio <40, f"ratio {ratio:.1f}, -16 for 4th order"
    print(f"-" * 55)
    print(f"CONVERGENCE RATIO {ratio:.2f} - 4th order confirmed")

if __name__ == "__main__":
    check_convergence()
    prompt_and_run() 
    
    
    
    
    
    
#Harmonic Ocsillator test
m = 1.0     #Mass (kg)
k_spring = 4.0 #Spring constant (N/m)
omega_sq = k_spring / m

# ODE derivative function: dy/dt = [v, -omega^2*x]
def harmonic_oscillator(y,t):
    x, v = y[0], y[1]
    dx_dt = v
    dv_dt = -omega_sq * x
    return np.array([dx_dt, dv_dt])

# Energy Calculation Funcation
def compute_energy(y, m=m, k=k_spring):
    x, v = y[0], y[1]
    kinetic = 0.5 * m * (v**2)
    potential = 0.5 * k * (x**2)
    return kinetic + potential

# simulation configuration

h = 0.1    #Time stpe size (seconds)
t_max = 10.0    #Total timem (seconds)
t = 0.0

# inital conditons: released from x0 = 1.0 m at rest (v) = 0.0 m/s)
y = np.array([1.0, 0.0])
E0 = compute_energy(y)

print(f"{'Time (t)':>8} | {'Position (x)':>13} | {'Velocity (v)':>13} | {'Energy (E)':>12} | {'Energy Drift (|E - E0|)':>23}")
print("-" * 78)

#log initial state
print(f"{t:>8.2f} | {y[0]:>13.6f} | {y[1]:>13.6f} | {E0:>12.6f} | {0.0:>23.4e}")

# Integration loop using RK4 call
while t< (t_max - 1e-9):
    current_h=min(h,t_max-t)
    y=rk4_step(harmonic_oscillator, y,t, current_h)
    t +=current_h
    
    current_energy = compute_energy(y)
    drift = abs(current_energy - E0)
    
    # Print every 1.0 seconds
    if np.isclose( t % 1.0, 0.0) or np.isclose(t % 1.0, 1.0):
        print(f"{t:>8.2f} | {y[0]:>13.6f} | {y[1]:>13.6f} | {current_energy:>12.6f} | {drift:>23.4e}")
        