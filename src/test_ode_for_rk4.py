import numpy as np
from integrate import rk4_step


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
    