import numpy as np
from dataclasses import dataclass, replace
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from integrate import rk4_step
from controller import CSTRCoolantPI, PIParams

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
    mc_target = Q_jacket/(p.Cp_coolant*(Tc_target - p.Tc_in)) #Coolant massflow rate (kg/min) T = target 
    return C_A, T_target, Tc_target, mc_target, conversion

def stability_margin(T_target, params=None):
    #Return dQgen_dT, dQremoved_dT per unit reactor volume (J/min*K*m^3)
    
    p = default_params() if params is None else params
    C_A, T, Tc_target, mc_target, X_A = solve_steady_state(T_target, p)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    dQgen_dT = (-p.delta_H_rxn)*p.F_A0*((X_A*(1-X_A))*(p.Ea_over_R/(T_target)**2))
    UAeff = (p.UA*mc_target*p.Cp_coolant)/(mc_target*p.Cp_coolant + p.UA)
    dQremoved_dT = p.rho*p.Cp_feed*p.v0 + UAeff
    return dQgen_dT / p.V, dQremoved_dT / p.V

def derivatives(y, t, p, mc):
    #Time derivatives [dCa/dt, dT/dt, dTc/dt], per minute.
    #y = [Ca (mol/m^3), T (K), Tc (K)]; qc = coolant flow (kg/min)
    C_A, T, Tc = y[0], y[1], y[2]
    k = rate_constant(T, p)
    dC_A_dt = ((p.C_A0 - C_A) / p.tau) - k*C_A
    beta_reactor = (-p.delta_H_rxn)/(p.rho*p.Cp_feed)
    gamma_reactor = (p.UA)/(p.V*p.rho*p.Cp_feed)
    dT_dt = ((p.T0 - T)/p.tau) + (beta_reactor*k*C_A) - (gamma_reactor*(T- Tc))
    gamma_coolant = (p.UA)/(p.Vc*p.rho_c*p.Cp_coolant)
    dTc_dt = (mc/(p.rho_c*p.Vc))*((p.Tc_in- Tc)) + (gamma_coolant*(T - Tc))
    return np.array([dC_A_dt, dT_dt, dTc_dt])

def solve_cstr_dynamic(y_initial, t_range, h, p, controller, seed, sigma_T, sigma_Tc, sigma_Ca, flow_frac):
    '''simulates a cstr with coolant flowrate PI controller with noise '''
    
    t_start, t_end = t_range                            #time in minutes
    t_points = np.arange(t_start, t_end+(h/2.0), h)     #time grid in minutes
    num_steps = len(t_points)
    y_curr = np.asarray(y_initial)
    state_dim = y_curr.shape[0]
    trajectory = np.empty((num_steps, state_dim), dtype=np.float64)
    measured = np.empty((num_steps, state_dim), dtype=np.float64)

    mc_history = np.empty((num_steps), dtype=np.float64)
    T_meas_history = np.empty((num_steps), dtype=np.float64)
    T_meas_history[0]=y_initial[1]
    measurement = y_initial[1]
    
    trajectory[0,:] = y_curr
    rng = np.random.default_rng(seed)
    sigma = np.array([sigma_Ca, sigma_T, sigma_Tc]) 
           


    #Move time forward
    for i in range(num_steps-1):
        t_curr = t_points[i]
        step_h = t_points[i + 1] - t_curr
        
        mc_val = controller.compute(measurement, dt=step_h) #controller
        mc_history[i] = mc_val
        
        y_curr = rk4_step(derivatives, y_curr, t_curr, step_h, p, mc_val)  #RK4 step

        trajectory[i+1,:] = y_curr
        measured = trajectory + rng.normal(0.0,sigma, size=trajectory.shape)
        measurement = measured[:,1]

        mc_history[i+1] = mc_val
        T_true = y_curr[1]
        Tc_true = y_curr[2]
        Ca_true = y_curr[0]
        qc_cmd = mc_history
        
    T_meas_history =  measured[:,1] 
    Tc_meas_history = measured[:,2]
    Ca_meas_history = measured[:,0]
    qc_meas_history = qc_cmd * (1.0 + rng.normal(0.0, flow_frac, size=mc_history.shape))
        
    return t_points, T_meas_history, Tc_meas_history, Ca_meas_history, qc_meas_history,
    T_true, Tc_true, Ca_true, qc_cmd

def simulate(duration=300.0, seed=0, dt=0.05, T_setpoint=400.0, params=None, pi_params=None, 
             fault=None, sigma_T=0.3, sigma_Tc=0.3, sigma_Ca=0.5, flow_frac = 0.03):
    '''simulating the reactor for 300 minutes '''
    p = default_params() if params is None else params
    C_A_ss, T_setpoint, Tc_ss, mc_ss, X_A_ss = solve_steady_state(T_setpoint,p)
    config = PIParams(u_bias=mc_ss, u_min=0.0, u_max=2*mc_ss)
    y0 = np.asarray([C_A_ss, T_setpoint, Tc_ss])
    t_range = (0.0, duration)                                   #simulation time in minutes
    
    controller = CSTRCoolantPI(config, setpoint = T_setpoint)
    
    (tgrid, T_measured, Tc_measured, Ca_measured, qc_measured, T_true, Tc_true,
     Ca_true, qc_cmd) = solve_cstr_dynamic(
        y0, t_range, dt, p, controller, seed, sigma_T, sigma_Tc, sigma_Ca, flow_frac
    )
    
    
    return ({"time": tgrid, "T": T_measured, "Tc": Tc_measured, "Ca": Ca_measured, "qc": qc_measured, 
             "T_true": T_true, "Tc_true": Tc_true,"Ca_true":Ca_true, "qc_cmd":qc_cmd })
    

if __name__ == "__main__":
    
    p = default_params()
    T_target = float(input("Enter target reactor temperture (K): "))
    C_A_ss, T_target, Tc_ss, mc_ss, X_A_ss = solve_steady_state(T_target,p)
    config = PIParams(u_bias=mc_ss, u_min=0.0, u_max=2*mc_ss)

    y = [C_A_ss, T_target, Tc_ss]
    y_b = [C_A_ss, T_target + 2.0, Tc_ss]         #b case: Temperature changed
    y_c = [C_A_ss, T_target -10.0, Tc_ss]         #c case: Temperature changed
    y_d = [C_A_ss, 475.0, Tc_ss]           #d case: (designed start up values)

    h = 0.05                         #time step or dt in minutes 
    t_range = (0.0, 60.0)            #simulate time in minutes
    seed=0                           #integer

    #Solve
    
    
    out = simulate()                #{"time":"T":"Tc":"Ca":"qc":"parameters_coupled"}

    print(out["tgrid"][-1], out["T_measured"][-1], out["Tc_measured"][-1], out["Ca_measured"][-1], out["qc_measured"][-1],out["parameters_coupled"][-1])

    
    
    
    
    '''Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states, mc_history = solve_cstr_dynamic(y, t_range, h, p, controller,seed)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states_b, mc_history_b = solve_cstr_dynamic(y_b, t_range, h, p, controller,seed)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states_c, mc_history_c = solve_cstr_dynamic(y_c, t_range, h, p, controller, seed)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states_d, mc_history_d = solve_cstr_dynamic(y_d, t_range, h, p, controller, seed)'''
    
    
    
    
    
    
    '''min_per_col = states.min(axis=0)
    max_per_col = states.max(axis=0)
    min_coolant_b = mc_history_b.min(axis=0)
    max_coolant_b = mc_history_b.max(axis=0)'''

    
    
    '''print(f"--- Steady-State Operating Point Verification at T = {T_target:.2f} K ---")
    print(f"Exit stream concentration ss:  {C_A_ss:.2f} mol/m^3")
    print(f"Conversion ss:                 {X_A_ss * 100:.2f} %")
    print(f"Heat Generated ss:             {Q_gen:.2f} J/min")
    print(f"Inlet Stream Load ss:          {Q_inlet:.2f} J/min")
    print(f"Required Jacket Duty ss:       {Q_jacket:.2f} J/min")
    print(f"Required Coolant Temp ss:      {Tc_ss:.2f} K ({Tc_ss - 273.15:.2f} °C)")
    print(f"Coolant Mass Flow Rate ss:     {mc_ss:.3f} kg/min\n")
    print(f"===================================================================")
    
    print(f"Final Coolant flow rate base T = 400:            {mc_history[-1]} kg/min")
    print(f"Final Concentration base T = 400:               {states[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp base T = 400:                {states[-1, 1]:.5f} K")
    print(f"Final Jacket Temp base T = 400:               {states[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states[:,1].min():.5f} K, Max = {states[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {mc_history.min(axis=0):.5f} kg/min, Max = {mc_history.max(axis=0):.5f} kg/min")
    
    print(f"===================================================================")
    print(f"Final Coolant flow rate B case T+2K:     {mc_history_b[-1]} kg/min")
    print(f"Final Concentration B case T+2K:         {states_b[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp B case T+2K:          {states_b[-1, 1]:.5f} K")
    print(f"Final Jacket Temp B case T+2K:           {states_b[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states_b[:,1].min():.5f} K, Max = {states_b[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {mc_history_b.min(axis=0):.5f} kg/min, Max = {mc_history_b.max(axis=0):.5f} kg/min")
    
    print(f"===================================================================")
    print(f"Final Coolant flow rate C case T-10K:     {mc_history_c[-1]} kg/min")
    print(f"Final Concentration C case T-10K:         {states_c[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp C case T-10K:          {states_c[-1, 1]:.5f} K")
    print(f"Final Jacket Temp C case T-10K:           {states_c[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states_c[:,1].min():.5f} K, Max = {states_c[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {mc_history_c.min(axis=0):.5f} kg/min, Max = {mc_history_c.max(axis=0):.5f} kg/min")
    
    print(f"===================================================================")
    print(f"Final Coolant flow rate D case T=475K:     {mc_history_d[-1]} kg/min")
    print(f"Final Concentration D case T=475K:         {states_d[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp D case T=475K:          {states_d[-1, 1]:.5f} K")
    print(f"Final Jacket Temp D case T=475K:           {states_d[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states_d[:,1].min():.5f} K, Max = {states_d[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {mc_history_d.min(axis=0):.5f} kg/min, Max = {mc_history_d.max(axis=0):.5f} kg/min")
    print(f"===================================================================")'''


