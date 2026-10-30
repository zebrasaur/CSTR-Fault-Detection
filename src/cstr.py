import numpy as np
from dataclasses import dataclass, replace
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from controller import PIParams, CSTRCoolantPI
from integrate import rk4_step
from faults import FaultType, FaultEvent, apply_sensor_faults, apply_actuator_faults, apply_process_faults

@dataclass(frozen=True)
class CSTRParams:
    '''   Reactor and Operating Parameters   '''
    V: float = 1.0          # reactor volume, m^3
    v0: float = 0.3         # volumetric flow rate (m^3/min)
    C_A0: float = 2500.0    #feed concentration (mol/m^3)
    T0: float = 300.0        #Feed reactant temperature (K)
    
        # Jacket and Coolant Properties
    Tc_in: float = 293.15   #Feed coolant temperature (K)
    Vc: float = 0.1195      # volume of coolant (m^3) using 3" half-pipe jacket
    Cp_coolant: float = 4184.0          #specific heat capacity of coolant (J/kg*K)
    UA: float = 600_000.0               #overall heat transfer capacity (J/min*K)
    rho_c: float = 1000.0               #fluid density of coolant (kg/m^3)

        # Fluid and Heat Transfer Properties
    Cp_feed: float = 4000.0             #specific heat capacity of feed (J/(kg*K))
    delta_H_rxn: float = -250_000.0     #Heat of reaction (J/mol) exothermic
    rho: float = 1000.0                 #fluid density (kg/m^3)
    
        # Kinetic Parameters: k(T) = k_ref * exp[(Ea/R) * (1/T_ref - 1/T)]
    k_ref: float = 0.0075       # Rate constant at T_ref (1/min)
    T_ref: float = 300.0        # Reference temperature (K)
    Ea_over_R: float = 6000.0   # Activation energy / gas constant (K)
    
    @property
    def tau(self):
        return self.V / self.v0          # space-time, min
    
    @property
    def F_A0(self):
        return self.v0*self.C_A0       # molar feed rate (mol/min)
    
def default_params():
    return CSTRParams()


#Arrhenius rate constant k(T), 1/min
def rate_constant(T, p):
    k = p.k_ref*np.exp(p.Ea_over_R*(1/(p.T_ref) - 1/T))
    return k

def heat_duties(T, p):
    k = rate_constant(T,p) #rate constant (1/min)
    conversion = (k*p.tau)/(1+k*p.tau) #fractional conversion calculation
    C_A = p.C_A0*(1 - conversion)      #exit stream concentration (mol/m^3)
    Q_gen = ((-p.delta_H_rxn))*(k*C_A*p.V) #Heat gen J/min
    Q_inlet = p.rho*p.Cp_feed*p.v0*(T - p.T0) #Heat duty J/min of inlet stream
    Q_jacket = Q_gen - Q_inlet #Heat duty J/min of cooling jacket 
    return Q_gen, Q_inlet, Q_jacket
    
    
def solve_steady_state(T_target, params=None):
    #Solve for the steady state properties
    
    p = default_params() if params is None else params
    k = rate_constant(T_target,p)
    conversion = (k*p.tau)/(1+k*p.tau) #fractional conversion calculation
    C_A = p.C_A0*(1 - conversion)      #exit stream concentration (mol/m^3)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    Tc_target = T_target - (Q_jacket/p.UA) #coolant temperature at jacket (K)
    qc_target = Q_jacket/(p.Cp_coolant*(Tc_target - p.Tc_in)) #Coolant massflow rate (kg/min) T = target 
    return C_A, T_target, Tc_target, qc_target, conversion

def stability_margin(T_target, params=None):
    #Return dQgen_dT, dQremoved_dT per unit reactor volume (J/min*K*m^3)
    
    p = default_params() if params is None else params
    C_A, T, Tc_target, qc_target, X_A = solve_steady_state(T_target, p)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    dQgen_dT = (-p.delta_H_rxn)*p.F_A0*((X_A*(1-X_A))*(p.Ea_over_R/(T_target)**2))
    UAeff = (p.UA*qc_target*p.Cp_coolant)/(qc_target*p.Cp_coolant + p.UA)
    dQremoved_dT = p.rho*p.Cp_feed*p.v0 + UAeff
    return dQgen_dT / p.V, dQremoved_dT / p.V

def derivatives(y, t, p, qc):
    #Time derivatives [dCa/dt, dT/dt, dTc/dt], per minute.
    #y = [Ca (mol/m^3), T (K), Tc (K)]; qc = coolant flow (kg/min)
    C_A, T, Tc = y[0], y[1], y[2]
    k = rate_constant(T, p)
    dC_A_dt = ((p.C_A0 - C_A) / p.tau) - k*C_A
    beta_reactor = (-p.delta_H_rxn)/(p.rho*p.Cp_feed)
    gamma_reactor = (p.UA)/(p.V*p.rho*p.Cp_feed)
    dT_dt = ((p.T0 - T)/p.tau) + (beta_reactor*k*C_A) - (gamma_reactor*(T- Tc))
    gamma_coolant = (p.UA)/(p.Vc*p.rho_c*p.Cp_coolant)
    dTc_dt = (qc/(p.rho_c*p.Vc))*((p.Tc_in- Tc)) + (gamma_coolant*(T - Tc))
    return np.array([dC_A_dt, dT_dt, dTc_dt])

def solve_cstr_dynamic(y_initial, t_range, h, p, controller, seed,
                       sigma_T, sigma_Tc, sigma_Ca, flow_frac,
                       faults: list[FaultEvent] | None = None):
    '''simulates a cstr with coolant flowrate PI controller with noise '''
    if faults is None:
        faults = []
    t_start, t_end = t_range                            #time in minutes
    t_points = np.arange(t_start, t_end+(h/2.0), h)     #time grid in minutes
    num_steps = len(t_points)
    y_curr = np.asarray(y_initial, dtype= np.float64)
    state_dim = y_curr.shape[0]
    trajectory = np.empty((num_steps, state_dim), dtype=np.float64)
    qc_cmd_history = np.empty((num_steps), dtype=np.float64)
    qc_actual_history = np.empty((num_steps), dtype=np.float64) 
    T_meas_history = np.empty((num_steps), dtype=np.float64)
    T_meas_history[0]=y_initial[1] 
    trajectory[0,:] = y_curr
    rng = np.random.default_rng(seed)
           
    #Move time forward
    for i in range(num_steps-1):
        t_curr = t_points[i]
        step_h = t_points[i + 1] - t_curr
        T_noisy = y_curr[1] + rng.normal(0.0, sigma_T)          #Temp sensor noise
        T_meas = apply_sensor_faults(T_noisy, t_curr, faults)   #Temp sensor faults
        T_meas_history[i] = T_meas
        
        qc_cmd = controller.compute(measurement=T_meas, dt=step_h) #controller
        qc_cmd_history[i] = qc_cmd
        qc_actual = apply_actuator_faults(qc_cmd, t_curr, faults)  #valve faults
        qc_actual_history[i] = qc_actual                           #actual coolant flow rate
        
        p_current = apply_process_faults(p, t_curr, faults)
        
        y_curr = rk4_step(derivatives, y_curr, t_curr, step_h, p_current, qc_actual)  #RK4 step

        trajectory[i+1,:] = y_curr
        
    qc_cmd_history[-1] = qc_cmd_history[-2]                          #last slot filled
    qc_actual_history[-1] = qc_actual_history[-2]                    #last slot filled
    T_meas_history[-1] = trajectory[-1,1]+rng.normal(0.0, sigma_T)+apply_sensor_faults(trajectory[-1,1], t_curr, faults) #last slot filled
          
    Tc_meas_history = trajectory[:, 2] + rng.normal(0.0, sigma_Tc, size=num_steps)
    Ca_meas_history = trajectory[:, 0] + rng.normal(0.0, sigma_Ca, size=num_steps)
    qc_meas_history = qc_actual_history * (1.0 + rng.normal(0.0, flow_frac, size=num_steps))
        
        
        
        
    return t_points, T_meas_history, Tc_meas_history, Ca_meas_history, qc_meas_history, trajectory, qc_cmd_history

def simulate(duration=300.0, T_setpoint=400.0, seed=0, dt=0.05, params=None, pi_params=None, 
             faults=None, sigma_T=0.3, sigma_Tc=0.3, sigma_Ca=0.03, flow_frac = 0.02):
    '''simulating the reactor for 300 minutes '''
    p = default_params() if params is None else params
    C_A_ss, T_setpoint, Tc_ss, qc_ss, X_A_ss = solve_steady_state(T_setpoint,p)
    
    if qc_ss <= 0 or Tc_ss >= T_setpoint:
        raise ValueError(f"Setpoint {T_setpoint} K is not achievable with cooling (needs coolant flow {qc_ss:.1f} kg/min).")
    
    config = PIParams(u_bias=qc_ss, u_min=0.0, u_max=2*qc_ss)
    y0 = np.asarray([C_A_ss, T_setpoint, Tc_ss])
    t_range = (0.0, duration)                                   #simulation time in minutes
    
    controller = CSTRCoolantPI(config, setpoint = T_setpoint)
    
    (tgrid, T_measured, Tc_measured, Ca_measured, qc_measured, trajectory, qc_cmd)=solve_cstr_dynamic(
        y0, t_range, dt, p, controller, seed, sigma_T, sigma_Tc, sigma_Ca, flow_frac, faults
    )
    Ca_true = trajectory[:,0]
    T_true = trajectory[:,1]
    Tc_true = trajectory[:,2]
    
    
    return ({"time": tgrid, "T": T_measured, "Tc": Tc_measured, "Ca": Ca_measured, "qc": qc_measured, 
             "T_true": T_true, "Tc_true": Tc_true,"Ca_true":Ca_true, "qc_cmd":qc_cmd })
    
    

