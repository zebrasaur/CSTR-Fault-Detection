from dataclasses import dataclass
import numpy as np



@dataclass(frozen=True)
class PIParams:
    u_bias: float                   # Nominal steady-state flow rate/minute (m_c,ss)
    u_max:  float                    # Maximum actuator limit/minute (e.g., 200% nominal)
    u_min:  float                    # Minimum actuator limit
    tau_1:  float = 4.1228           # Min
    theta:  float = 1.6136           # Min, apparent dead time
    K_process: float = -0.5489      # K per (kg/min)
    tau_c_factor: float = 1.5       # SIMC design factor between theta < tau_c < 2*theta
  
    @property
    def tau_c(self):                 
      return self.tau_c_factor*self.theta

    @property
    def Kc(self):
      return self.tau_1 / ((abs(self.K_process)) * (self.tau_c + self.theta))

    @property
    def tau_I(self):
      return min(self.tau_1, (4 * (self.tau_c + self.theta)))



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
