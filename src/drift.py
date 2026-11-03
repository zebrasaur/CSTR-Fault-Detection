from dataclasses import dataclass
import numpy as np

"""Bounded Mean-Reverting Ornstein-Uhlenbeck process generator for CSTR disturbances."""

@dataclass (frozen=True)
class DriftVariableConfig:
  mean: float
  sigma_stat: float  #expected deviation magnitude
  tau_rev: float     #Reversion time constant (minutes)
  val_min: float
  val_max: float


class BoundedProcessDrift:

  def __init__(
      self,
      configs: dict[str, DriftVariableConfig],
      rng):
    self.configs = configs
    self.rng = rng 
        
    '''Initialize variables at their nominal means'''
    self.states: dict[str, float] = {k: cfg.mean for k, cfg in configs.items()}


  def step(self, dt: float) -> dict[str, float]:
    """Advances each drift variable forward across time step dt."""
    

    for key, cfg in self.configs.items():
      current_val = self.states[key]
      theta = 1.0 / max(cfg.tau_rev, 1e-6)
      decay = np.exp(-theta * dt)
      sigma_step = cfg.sigma_stat * np.sqrt(max(0.0, 1.0 - np.exp(-2.0 * theta * dt)))


      # Exact discrete transition coefficients

      # Propagate Gaussian shock
      shock = self.rng.normal(loc=0.0, scale=sigma_step)
      next_val = cfg.mean + (current_val - cfg.mean) * decay + shock

      # Enforce physical bounding box
      self.states[key] = float(np.clip(next_val, cfg.val_min, cfg.val_max))

    return self.states.copy()
