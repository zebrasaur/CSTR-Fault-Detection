import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --- Reactor and Operating Parameters ---
V = 1.0  # Reactor volume (m^3)
v0 = 0.3  # Volumetric flow rate (m^3/min)
tau = V / v0  # Space time (min)

C_A0 = 2500.0  # Feed concentration (mol/m^3)
F_A0 = v0 * C_A0  # Molar feed rate (mol/min)
T0 = 300.0  # Feed reactant temperature (K)
Tc_in = 293.15 # Feed Coolant temperature (K)

# Fluid and Heat Transfer Properties
Cp = 4000  # specific heat capacity of feed (J/(kg*K))
Cpc = 4184 # specific heat capacity of coolant (J/(kg*K))
UA = 600000.00 # Overall heat transfer capacity (J/min*K)
delta_H_rxn = -250_000.0  # Heat of reaction (J/mol, exothermic)
rho = 1000 # Fluid density (kg/m^3)

# Kinetic Parameters: k(T) = k_ref * exp[(Ea/R) * (1/T_ref - 1/T)]
k_ref = 0.0075  # Rate constant at T_ref (1/min)
T_ref = 300.0  # Reference temperature (K)
Ea_over_R = 6000.0  # Activation energy / gas constant (K)

# --- Temperature Grid ---
T = np.linspace(300.0, 450.0, 500)  # Reactor Temperature range (K)

# rate constant calculation
k_400 =  k_ref*np.exp(Ea_over_R*(1/T_ref- 1/400)) #rate at T = 400K
k = k_ref*np.exp(Ea_over_R*(1/T_ref - 1/T))

#fractional conversion calculation
X_A_400 = (k_400*tau)/(1+k_400*tau)
X_A = (k*tau)/(1+k*tau)

# exit stream concentration
C_A_400 = C_A0*(1 - X_A_400)
C_A = C_A0*(1 - X_A)

# heat generation calculation
Q_gen_400 = (-delta_H_rxn)*(k_400*C_A_400*V)     #Heat gen J/min at T = 400K
Q_gen = ((-delta_H_rxn)*(k*C_A*V))               #Heat gen J/min

#heat removal calculation

Q_inlet_400 = rho*Cp*v0*(400 - T0)              #Heat duty J/min of inlet stream at T = 400K
Q_jacket_400 = Q_gen_400 - Q_inlet_400          #Heat duty J/min of cooling jacket T = 400K    
Tc_400 = 400 - (Q_jacket_400/UA)                #Jacket Temperature at T = 400K
mc_400 = Q_jacket_400/(Cpc*(Tc_400 - Tc_in))    #Coolant mass flow rate T = 400K
Q_rem_Tc = (rho*Cp*v0*(T - T0) + UA*(T - Tc_400))  #Heat removal J/min
UAeff = (UA*mc_400*Cpc)/(mc_400*Cpc+ UA)
Q_rem_mc = (rho*Cp*v0*(T - T0)) + UAeff*(T - Tc_in)

print(f"--- Operating Point Verification at T = 400 K ---")
print(f"Conversion X_A:          {X_A_400 * 100:.2f}%")
print(f"Heat Generated:          {Q_gen_400:.2f} J/min")
print(f"Inlet Stream Load:       {Q_inlet_400:.2f} J/min")
print(f"Required Jacket Duty:    {Q_jacket_400:.2f} J/min")
print(f"Required Coolant Temp:   {Tc_400:.2f} K ({Tc_400 - 273.15:.2f} °C)")
print(f"Coolant Mass Flow Rate:  {mc_400:.3f} kg/min\n")


# --- Plotting ---
plt.figure(figsize=(8, 5))
plt.plot(T, Q_gen, "r-", linewidth=2, label="Q_gen (T): Heat Generation")
plt.plot(T, Q_rem_Tc, "b-", linewidth=2, label="Q_rem_Tc (T): Heat Removal (Fixed $T_c$)")
plt.plot(T, Q_rem_mc, "g-", linewidth=2, label="Q_rem_mc (T): Heat Removal (Fixed $mc$)")

plt.title("Van Heerden Diagram for Jacketed CSTR")
plt.xlabel("Reactor Temperature $T$ (K)")
plt.ylabel("Heat Rate (J/min)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(Path(__file__).resolve().parent.parent / "figures" / "van_heerden_400K.png", dpi=150)
plt.show()

