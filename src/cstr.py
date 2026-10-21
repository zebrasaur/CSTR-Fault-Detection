import numpy as np
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class CSTRParams:
        # --- Reactor and Operating Parameters ---
    V: float = 1.0          # reactor volume, m^3
    v0: float = 0.3         # volumetric flow rate (m^3/min)
    C_A0: float = 2500.0    #feed concentration (mol/m^3)
    T0: float = 300.0        #Feed reactant temperature (K)
    Tc_in: float = 293.15   #Feed coolant temperature (K)

        # Fluid and Heat Transfer Properties
    Cp_feed: float = 4000.0             #specific heat capacity of feed (J/(kg*K))
    Cp_coolant: float = 4184.0          #specific heat capacity of coolant (J/kg*K)
    UA: float = 600_000.0               #overall heat transfer capacity (J/min*K)
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

def heat_duties(T, params=None):
    p = default_params() if params is None else params
    k = rate_constant(T,p) #rate constant (1/min)
    conversion = (k*p.tau)/(1+k*p.tau) #fractional conversion calculation
    C_A = p.C_A0*(1 - conversion)      #exit stream concentration (mol/m^3)
    Q_gen = ((-p.delta_H_rxn))*(k*C_A*p.V) #Heat gen J/min
    Q_inlet = p.rho*p.Cp_feed*p.v0*(T - p.T0) #Heat duty J/min of inlet stream
    Q_jacket = Q_gen - Q_inlet #Heat duty J/min of cooling jacket 
    return Q_gen, Q_inlet, Q_jacket
    
    
def solve_steady_state(T_target, params=None):
    p = default_params() if params is None else params
    k = rate_constant(T_target,p)
    conversion = (k*p.tau)/(1+k*p.tau) #fractional conversion calculation
    C_A = p.C_A0*(1 - conversion)      #exit stream concentration (mol/m^3)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    Tc_target = T_target - (Q_jacket/p.UA) #coolant temperature at jacket (K)
    mc_target = Q_jacket/(p.Cp_coolant*(Tc_target - p.Tc_in)) #Coolant massflow rate (kg/min) T = target 
    return C_A, T_target, Tc_target, mc_target, conversion

def stability_margin(T_target, params=None):
    """ Return dQgen_dT, dQremoved_dT per unit reactor volume (J/min*K*m^3)"""
    p = default_params() if params is None else params
    C_A, T, Tc_target, mc_target, X_A = solve_steady_state(T_target, p)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    dQgen_dT = (-p.delta_H_rxn)*p.F_A0*((X_A*(1-X_A))*(p.Ea_over_R/(T_target)**2))
    UAeff = (p.UA*mc_target*p.Cp_coolant)/(mc_target*p.Cp_coolant + p.UA)
    dQremoved_dT = p.rho*p.Cp_feed*p.v0 + UAeff
    return dQgen_dT / p.V, dQremoved_dT / p.V


if __name__ == "__main__":
    T_target = float(input("Enter target reactor temperture (K): "))
    C_A, T_target, Tc, mc, X_A = solve_steady_state(T_target)
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target)



    print(f"--- Operating Point Verification at T = {T_target:.2f} K ---")
    print(f"Exit stream concentration:  {C_A:.2f} mol/m^3")
    print(f"Conversion:                 {X_A * 100:.2f} %")
    print(f"Heat Generated:             {Q_gen:.2f} J/min")
    print(f"Inlet Stream Load:          {Q_inlet:.2f} J/min")
    print(f"Required Jacket Duty:       {Q_jacket:.2f} J/min")
    print(f"Required Coolant Temp:      {Tc:.2f} K ({Tc - 273.15:.2f} °C)")
    print(f"Coolant Mass Flow Rate:     {mc:.3f} kg/min\n")

