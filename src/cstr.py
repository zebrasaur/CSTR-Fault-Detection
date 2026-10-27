import numpy as np
from dataclasses import dataclass, replace
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from integrate import rk4_step
from controller import CSTRCoolantPI, PIParams




@dataclass(frozen=True)
class CSTRParams:
        # Reactor and Operating Parameters
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

config = PIParams()
p = default_params()       



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

def solve_cstr_dynamic(y_initial, t_range, h, mc, p=p):
    '''simulates the cstr using a 2D trajectory array'''
    
    t_start, t_end = t_range        #time in minutes
    t_points = np.arange(t_start, t_end+(h/2.0), h) #time grid in minutes
    num_steps = len(t_points)
    y_curr = np.asarray(y_initial)
    state_dim = y_curr.shape[0]
    trajectory = np.empty((num_steps, state_dim), dtype=np.float64)
    mc_history = np.empty((num_steps, state_dim), dtype=np.float64)
    Kc_history = np.empty((num_steps, state_dim), dtype=np.float64)
    tauI_history = np.empty((num_steps, state_dim), dtype=np.float64)
    
    controller = CSTRCoolantPI(config, setpoint = 400.0)

    trajectory[0,:] = y_curr
    mc_history[0] = controller.cfg.u_bias
    Kc_history[0] = controller.cfg.Kc
    tauI_history[0] = controller.cfg.tau_I

    #Move time forward
    for i in range(num_steps-1):
        t_curr = t_points[i]
        step_h = t_points[i + 1] - t_curr
        current_temp = y_curr[1]
        temp_error = abs(current_temp - controller.setpoint)
        
        mc_val = controller.compute(measurement=current_temp, dt=step_h)
        mc_history[i] = mc_val
        
        y_curr = rk4_step(derivatives, y_curr, t_curr, step_h, p, mc_val)  #RK4 step
        
        dmc = mc_val - mc
        Kp = temp_error/dmc
        y_third = 0.2835                       #smith 2 point fit 1/3
        y_full = 0.6321                       #smith 2 point fit 1.0
        y_28 = controller.setpoint + y_third*temp_error
        y_63 = controller.setpoint + y_full*temp_error
        t_28 = t_points[i]
        t_63 = t_points[i]

        tau_1 = 1.5*(t_63 - t_28)
        theta = t_63 - tau_1
        tau_c = 1.5*theta
        Kc = tau_1 / ( abs(Kp)*(tau_c + theta) )
        tau_I = min(tau_1 ,4*(tau_c + theta) )
        controller.cfg.Kc = Kc
        controller.cfg.tau_I = tau_I
        Kc_history[i] = controller.cfg.Kc
        tauI_history[i] = controller.cfg.tau_I

        trajectory[i+1,:] = y_curr
        
    return t_points, trajectory, mc_history, Kc_history, tauI_history



if __name__ == "__main__":
    T_target = float(input("Enter target reactor temperture (K): "))
    p = default_params()
    C_A, T_target, Tc, mc, X_A = solve_steady_state(T_target,p)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    y = [C_A, T_target, Tc]
    residual = derivatives(np.array(y), 0.0, p, mc)
    h = 0.05                          #time step or dt in minutes 
    t_range = (0.0, 60.0)            #simulate time in minutes
    mc_step = mc*(1+0.03)

    time, states, mc_history, Kc_history, tauI_history = solve_cstr_dynamic(y, t_range, h, mc_step, p)
    


    print(f"--- Operating Point Verification at T = {T_target:.2f} K ---")
    print(f"Exit stream concentration:  {C_A:.2f} mol/m^3")
    print(f"Conversion:                 {X_A * 100:.2f} %")
    print(f"Heat Generated:             {Q_gen:.2f} J/min")
    print(f"Inlet Stream Load:          {Q_inlet:.2f} J/min")
    print(f"Required Jacket Duty:       {Q_jacket:.2f} J/min")
    print(f"Required Coolant Temp:      {Tc:.2f} K ({Tc - 273.15:.2f} °C)")
    print(f"Coolant Mass Flow Rate:     {mc:.3f} kg/min\n")
    print(f":dC_A_dt, dT_dt, dTc_dt     {residual}")
    print(f"===================================================================")
    print(f"mc_step =  {mc_step}")
    print(f"Final Concentration :         {states[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp :          {states[-1, 1]:.5f} K")
    print(f"Final Jacket Temp :           {states[-1, 2]:.5f} K")
    print(f"Final mc value:               {mc_history[-1, 0]:.5f} mol/m^3")
    print(f"Final Kc value:               {Kc_history[-1, 0]:.5f} K")
    print(f"Final tau_I value:            {tauI_history[-1, 0]:.5f} K")

