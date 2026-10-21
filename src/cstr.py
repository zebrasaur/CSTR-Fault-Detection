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
    def F_A0(self):
        return self.v0 / self.C_A0       # molar feed rate (mol/min)
    
def default_params():
    return CSTRParams()


