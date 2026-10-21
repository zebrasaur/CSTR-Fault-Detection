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



T_target = float(input("Enter target reactor temperture (K): "))

#Arrhenius rate constant k(T), 1/min
def rate_constant(T, p):
    k = p.k_ref*np.exp(p.Ea_over_R*(1/(p.T_ref) - 1/T))
    return k

def solve_steady_state(T_target, params=None):
    #return (Ca mol/m^3, T(K), Tc(K), mc(kg/min), conversion()) at temperture T_target
    p = default_params() if params is None else params
    k = rate_constant(T_target,p)
    conversion = (k*p.tau)/(1+k*p.tau) #fractional conversion calculation
    C_A = p.C_A0*(1 - conversion)      #exit stream concentration (mol/m^3)
    Q_gen = ((-p.delta_H_rxn))*(k*C_A*p.V) #Heat gen J/min
    Q_inlet = p.rho*p.Cp_feed*p.v0*(T_target - p.T0) #Heat duty J/min of inlet stream at T = 400K
    Q_jacket = Q_gen - Q_inlet #Heat duty J/min of cooling jacket T = 400K 
    Tc_target = T_target - (Q_jacket/p.UA) #coolant temperature at jacket (K)
    mc_target = Q_jacket/(p.Cp_coolant*(Tc_target - p.Tc_in)) #Coolant massflow rate (kg/min) T = target 
    Q_rem_Tc = (p.rho*p.Cp_feed*p.v0*(T_target - p.T0) + p.UA*(T_target - Tc_target))  #Heat removal J/min Tc fixed
    UAeff = (p.UA*mc_target*p.Cp_coolant)/(mc_target*p.Cp_coolant + p.UA)
    Q_rem_mc = (p.rho*p.Cp_coolant*p.v0*(T_target - p.T0)) + UAeff*(T_target - p.Tc_in) #Heat removal J/min mc fixed
    return conversion, C_A, Q_gen, Q_inlet, Q_jacket, Tc_target, mc_target

X, Ca, Qgen, Qinlet, Qjacket, Tc, mc = solve_steady_state(T_target)


print(f"--- Operating Point Verification at T = {T_target:.2f} K ---")
print(f"Conversion X_A:             {X * 100:.2f}%")
print(f"Exit stream concentration:  {Ca:.2f} mol/m^3")
print(f"Heat Generated:             {Qgen:.2f} J/min")
print(f"Inlet Stream Load:          {Qinlet:.2f} J/min")
print(f"Required Jacket Duty:       {Qjacket:.2f} J/min")
print(f"Required Coolant Temp:      {Tc:.2f} K ({Tc - 273.15:.2f} °C)")
print(f"Coolant Mass Flow Rate:     {mc:.3f} kg/min\n")

