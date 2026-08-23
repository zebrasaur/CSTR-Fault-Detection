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
