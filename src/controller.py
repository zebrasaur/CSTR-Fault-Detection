from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)

class PIParams:
    Kc: float = 1.8619 # Proportional gain: kg/(minute*K)
    tau_I: float = 4.1228 # Integral time constant:  minute
    u_bias: float = 109.0559  # Nominal steady-state flow rate/minute (m_c,ss)
    u_min: float = 0.0  # Minimum actuator limit
    u_max: float = 218.1118  # Maximum actuator limit/minute (e.g., 200% nominal)
  
  

class CSTRCoolantPI:

   def __init__(self, config: PIParams, setpoint):
    self.cfg = config
    self.setpoint = setpoint
    self.integral = 0.0

   def reset(self, initial_integral= 0.0):
    self.integral = initial_integral

   def compute(self, measurement, dt):
    """Calculates clamped coolant flow rate mc(t) using conditional anti-windup."""
    # Direct acting: e(t) = T - T_setpoint > 0 demands higher coolant flow
    error = measurement - self.setpoint

    # 1. Proportional term
    p_term = self.cfg.Kc * error


    # 3. Integral candidate
    if self.cfg.tau_I > 0.0:
      i_term = (self.cfg.Kc / self.cfg.tau_I) * self.integral
    else:
      i_term = 0.0

    # 4. Raw unclamped signal
    u_raw = self.cfg.u_bias + p_term + i_term 

    # 5. Actuator clamping
    u_clamped = np.clip(u_raw, self.cfg.u_min, self.cfg.u_max)

    # 6. Clamping Anti-Windup: freeze integration if saturated in direction of error
    is_set_high = u_raw >= self.cfg.u_max and error > 0.0
    is_set_low = u_raw <= self.cfg.u_min and error < 0.0

    if not (is_set_high or is_set_low) and self.cfg.tau_I > 0.0:
      self.integral += error * dt

    return u_clamped
