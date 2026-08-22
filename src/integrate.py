import numpy as np


def rk4_step(f, y, t, h):
    """
    f: function returning dy/dt
    y: current state vector
    t: current time
    h: time step size
    """

    k1 = f(y, t)
    k2 = f(y + (0.5 * h * k1), t + 0.5 * h)
    k3 = f(y + (0.5 * h * k2), t + 0.5 * h)
    k4 = f(y + h * k3, t + h)
    delta_y = (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
    y_next = y + delta_y
    return y_next


def system_ode(y, t):
    return -0.5 * y

if __name__ == "__main__":
    y0 = np.array([100.0])
    t0 = 0.0
    step_size = 0.1

    y1 = rk4_step(system_ode, y0, t0, step_size)

    print(f"Time t = {t0}: y = {y0[0]:.4f}")
    print(f"Time t = {t0 + step_size}: y = {y1[0]:.4f}")
    
    