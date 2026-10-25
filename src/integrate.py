import numpy as np

def rk4_step(f, y: np.ndarray, t: float, h: float, *args):
    """
    f: function returning dy/dt
    y: current state vector
    t: current time
    h: time step size
    """

    k1 = f(y, t, *args)
    k2 = f(y + (0.5 * h * k1), t + 0.5 * h, *args)
    k3 = f(y + (0.5 * h * k2), t + 0.5 * h, *args)
    k4 = f(y + h * k3, t + h, *args)
    delta_y = (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
    y_next = y + delta_y
    return y_next
