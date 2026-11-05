from dataclasses import dataclass, replace, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np

class FaultType(str, Enum):
    PUMP_TRIP = "pump_trip"                 #Coolant flow drops by fraction [0, 1]
    VALVE_FREEZE = "valve_freeze"           #Valve locks at specific mass flow rate
    FOULING = "fouling"                     #UA drops abruptly or ramps down
    FEED_TEMP_SURGE = "feed_temp_surge"     #T0 shifts by a delta T (K)
    FEED_CONC_SURGE = "feed_conc_surge"     #CA0 shifts by delta C (mol/m^3)
    SENSOR_BIAS_TEMP = "sensor_bias_temp"   #Constant offset (K)
    SENSOR_DRIFT = "sensor_drift"           #Linear drift added to T_meas over time
    FEED_TEMP_RAMP = "feed_temp_ramp"       #continuous ramp rate in T0 (K/min)
    FEED_CONC_RAMP = "feed_conc_ramp"       #continuous ramp rate in CA0 (mol/m^3*min)
    NONE = "none"


        
@dataclass(frozen=True)
class FaultEvent:
    fault_type: FaultType
    t_start: float                       #when faults start
    t_end: float = np.inf                #when faults clear (min) (np.inf if permaent)
    ramp_duration: float = 3*1440.0      #3 days. Abrupt step = 0.0 and Gradual ramp >= 0.0 (minutes)
    severity: float = 0.0
    
    def get_severity_factor(self, t):
        '''Calculates the severity scalar (zero to severity) accounting for ramps and recovery'''
        if t < self.t_start or t >= self.t_end:
            return 0.0
        if self.ramp_duration <= 0.0:
            return self.severity
        elapsed = t - self.t_start
        if elapsed >= self.ramp_duration:
            return self.severity
        return self.severity*(elapsed/self.ramp_duration)
    

def apply_sensor_faults(T_noisy, t,  faults: list[FaultEvent], fault_onset, severity):
    """Corrupts temperature fed to controller"""
    if not faults:
        return T_noisy
    T_meas = T_noisy
    for f in faults:
      if f.fault_type == FaultType.SENSOR_BIAS_TEMP:
        f.t_start=fault_onset
        f.severity = severity
        T_meas += f.get_severity_factor(t)      #severity of + factor (K)          
      elif f.fault_type == FaultType.SENSOR_DRIFT:
          if f.t_start <= t < f.t_end:
              T_meas += f.severity*(t - f.t_start)  #severity of + factor (K)           
    return T_meas

def apply_actuator_faults(qc_cmd, t, faults: list[FaultEvent], fault_onset, severity):
    """Apply actuator faults to the coolant-flow command."""
    if not faults: 
      return float(np.clip(qc_cmd, 0.0, None))
    qc_actual = qc_cmd
    for f in faults:
      if f.fault_type == FaultType.PUMP_TRIP:        #severity of 1.0 = 100% loss(kg/min)
        f.t_start=fault_onset
        f.severity = severity
        loss_fraction = f.get_severity_factor(t)   #severity of 0.6 = 60% loss
        qc_actual *= 1.0 - loss_fraction
      elif f.fault_type == FaultType.VALVE_FREEZE:   
        if f.t_start <= t< f.t_end:
            qc_actual = f.severity                   #severity holds fixed flow rate
    return float(np.clip(qc_actual, 0.0, None))

def apply_process_faults(p, t, faults: list[FaultEvent], fault_onset, severity):
    """Apply process faults to plant parameters"""
    if not faults:
        return p
    p_active = p
    for f in faults:
        if f.fault_type == FaultType.FOULING:
            f.t_start=fault_onset
            f.severity = severity
            factor = f.get_severity_factor(t)
            p_active = replace(p_active, UA=(p.UA*(1.0 - factor)))      #severity of 0.4 = 40% reduction in conductance
        elif f.fault_type == FaultType.FEED_TEMP_SURGE:
            factor = f.get_severity_factor(t)
            p_active = replace(p_active, T0 = (p.T0 + factor))          #severity of + factor (K)
        elif f.fault_type == FaultType.FEED_CONC_SURGE:
            factor = f.get_severity_factor(t)
            p_active = replace(p_active, C_A0 = (p.C_A0 + factor))      #severity of + factor (mol/m^3)
        elif f.fault_type == FaultType.FEED_TEMP_RAMP:
          if f.t_start <= t < f.t_end:
            factor = f.get_severity_factor(t)
            t_drift = f.severity * (t - f.t_start)                      #severity is K/min
            p_active = replace(p_active, T0=p.T0 + t_drift)
        elif f.fault_type == FaultType.FEED_CONC_RAMP:
            if f.t_start <= t < f.t_end:
                factor = f.get_severity_factor(t)
                ca_drift = f.severity * (t - f.t_start)                 #severity is mol/(m^3*min)
                p_active = replace(p_active, C_A0 = p.C_A0 + ca_drift)
                
    return p_active

