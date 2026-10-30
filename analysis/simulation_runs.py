from dataclasses import dataclass, replace
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import numpy as np
from cstr import simulate, default_params, CSTRParams
from fault_scenarios import pump_failure_test, heat_exchanger_fouling_test, compound_test 
from controller import pi_params


                #DEFINE FAULT NAMES
FAULT_SCENARIOS = {
    "none": (None, "None"),
    "pump": (pump_failure_test, "Pump Trip"),
    "fouling": (heat_exchanger_fouling_test, "Fouling"),
    "compound": (compound_test, "Compound"),
}


                #START OF PROMPT ASKS

def ask_reactor_params(default_fn=default_params) -> CSTRParams:
  """Prompts for parameter overrides; falls back to default_params() if empty."""
  p = default_fn()

  prompt_str = (
      "Enter modified reactor parameters (e.g. UA=500000, T0=305) "
      "(Press Enter for default): "
  )
  raw = input(prompt_str).strip()

  # If user pressed Enter or typed 'none', return default parameters unchanged
  if not raw or raw.lower() == "none":
    return p

  # Allow comma-separated or space-separated key=value overrides
  # Example: "UA=550000, T0=305"
  overrides = {}
  pairs = raw.replace(";", ",").split(",")
  for pair in pairs:
    pair = pair.strip()
    if not pair or "=" not in pair:
      continue
    key, val_str = pair.split("=", 1)
    key = key.strip()
    val_str = val_str.strip()

    if not hasattr(p, key):
      print(f"Warning: '{key}' is not a valid CSTRParams attribute. Skipping.")
      continue

    try:
      # Cast to float (or int if appropriate)
      overrides[key] = float(val_str)
    except ValueError:
      print(
          f"Warning: Could not parse value '{val_str}' for '{key}'. Skipping."
      )

  if overrides:
    # Works for both mutable and frozen dataclasses
    p = replace(p, **overrides)
    print(f"Applied overrides: {overrides}")

  return p


def ask_faults(prompt: str, default: str = "none"):   
  # All keys are now strings, so join works cleanly
  options = "/".join(FAULT_SCENARIOS.keys())

  # Normalize default in case None or uppercase is passed
  default_key = "none" if (default is None or default == "") else str(default).lower()

  raw = (
      input(f"{prompt} [{options}] (Press Enter for '{default_key}'): ")
      .strip()
      .lower()
  )

  # Fallback to default if user just pressed Enter
  chosen_key = raw if raw else default_key

  # Validate against available scenario keys
  if chosen_key not in FAULT_SCENARIOS:
    print(f"Unknown scenario '{raw}'. Falling back to '{default_key}'.")
    chosen_key = default_key

  return FAULT_SCENARIOS[chosen_key]  # Returns (fault_list, display_label)

def ask_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} (Press Enter for {default}): ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"Invalid number entered. Falling back to default: {default}")
        return default
    
def ask_int(prompt: str, default: int = 0) -> int:
  raw = input(f"{prompt} (Press Enter for {default}): ").strip()
  if not raw:
    return default
  try:
    return int(raw)
  except ValueError:
    print(f"Invalid integer entered. Falling back to default: {default}")
    return default

                    #PRINT INPUTED VALUES
def print_table(setpoint, duration, h, seed, fault_label, sigma_T, sigma_Tc, sigma_Ca, flow_frac):
    
    header = (
      f"{'Set Temp (K)':>12} | {'Duration':>10} | {'delta t':>9} | {'Seed':>6} | "
      f"{'Faults':>12} | {'Sigma T':>9} | {'Sigma Tc':>9} | {'Sigma Ca':>10} | {'Flow Frac':>10}"
  )
    
    divider = ("-" * 113)
    
    values = (
      f"{setpoint:>12.2f} | {duration:>10.1f} | {h:>9.4f} | {seed:>6d} | "
      f"{fault_label:>12s} | {sigma_T:>9.3f} | {sigma_Tc:>9.3f} | {sigma_Ca:>10.4f} | {flow_frac:>10.3f}"
  )
    print("\n" + header)
    print(divider)
    print(values + "\n")

                    #PROMPT FUNCTION
def prompt_and_run() -> dict:
    print("=== CSTR Simulation Configuration ===")
    setpoint = ask_float("Enter target reactor temperture (K): ", default=400)
    duration = ask_float("Enter simulation time (min)):  ", default=300)
    h = ask_float("Enter simulation dt = step size: ", default=0.05)
    seed = ask_int("Enter seed value (must be integer!): ", default= 0)
    params = ask_reactor_params()   #prompt for modified CSTR parameters(none=default)
    fault_list, fault_label = ask_faults("Enter test faults: ", default="none") #pump, fouling, compound
    sigma_T = ask_float("Enter reactor Temperature sigma: ", default=0.3)
    sigma_Tc = ask_float("Enter coolant Temperature sigma: ", default=0.3)
    sigma_Ca = ask_float("Enter concentration sigma: ", default=0.03)
    flow_frac = ask_float("Enter valve flow_frac: ", default=0.02)
    

    print_table(setpoint, duration, h, seed, fault_label, sigma_T, sigma_Tc, sigma_Ca, flow_frac)

    return {
      "duration": duration,
      "T_setpoint": setpoint,
      "seed": seed,
      "dt": h,
      "params": params,
      "pi_params": None,
      "faults": fault_list,
      "sigma_T": sigma_T,
      "sigma_Tc": sigma_Tc,
      "sigma_Ca": sigma_Ca,
      "flow_frac": flow_frac,
  }

#Solve

'''
Input:(duration=300.0, T_setpoint=400.0, seed=0, dt=0.05, params=None, pi_params=None, 
fault=None, sigma_T=0.3, sigma_Tc=0.3, sigma_Ca=0.03, flow_frac = 0.02)

Output: {"time":"T":"Tc":"Ca":"qc":"T_true":"Tc_true":"Ca_true":"qc_cmd"}
'''
cfg = prompt_and_run()
out = simulate(**cfg)  


print(f"Final time:                                      {out['time'][-1]:.5f} min")
print(f"Final Measured Reactor Temperature:              {out['T'][-1]:.5f} K")
print(f"Final Measured Coolant Temperature:              {out['Tc'][-1]:.5f} K")
print(f"Final Measured Effluent Concentration:           {out['Ca'][-1]:.5f} mol/m^3")
print(f"Final Measured Coolant flow rate:                {out['qc'][-1]:.5f} kg/min")
print(f"Final Designed Reactor Temperature:              {out['T_true'][-1]:.5f} K")
print(f"Final Designed Coolant Temperature:              {out['Tc_true'][-1]:.5f} K")
print(f"Final Designed Effluent Concentration:           {out['Ca_true'][-1]:.5f} mol/m^3")
print(f"Final Commanded Coolant flow rate:               {out['qc_cmd'][-1]:.5f} kg/min")
    
    
    
# Old calculations and prints here
    
'''C_A_ss, T_target, Tc_ss, qc_ss, X_A_ss = solve_steady_state(T_target,p)

    #y = [C_A_ss, T_target, Tc_ss]
    #y_b = [C_A_ss, T_target + 2.0, Tc_ss]         #b case: Temperature changed
    #y_c = [C_A_ss, T_target -10.0, Tc_ss]         #c case: Temperature changed
    #y_d = [C_A_ss, 475.0, Tc_ss]                  #d case: (designed start up values)


    
    Q_gen, Q_inlet, Q_jacket = heat_duties(T_target,p)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states, qc_history = solve_cstr_dynamic(y, t_range, h, p, controller,seed)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states_b, qc_history_b = solve_cstr_dynamic(y_b, t_range, h, p, controller,seed)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states_c, qc_history_c = solve_cstr_dynamic(y_c, t_range, h, p, controller, seed)
    
    controller = CSTRCoolantPI(config, setpoint = T_target)
    time, states_d, qc_history_d = solve_cstr_dynamic(y_d, t_range, h, p, controller, seed)
'''
    
'''min_per_col = states.min(axis=0)
    max_per_col = states.max(axis=0)
    min_coolant_b = qc_history_b.min(axis=0)
    max_coolant_b = qc_history_b.max(axis=0)'''    
    
'''print(f"--- Steady-State Operating Point Verification at T = {T_target:.2f} K ---")
    print(f"Exit stream concentration ss:  {C_A_ss:.2f} mol/m^3")
    print(f"Conversion ss:                 {X_A_ss * 100:.2f} %")
    print(f"Heat Generated ss:             {Q_gen:.2f} J/min")
    print(f"Inlet Stream Load ss:          {Q_inlet:.2f} J/min")
    print(f"Required Jacket Duty ss:       {Q_jacket:.2f} J/min")
    print(f"Required Coolant Temp ss:      {Tc_ss:.2f} K ({Tc_ss - 273.15:.2f} °C)")
    print(f"Coolant Mass Flow Rate ss:     {qc_ss:.3f} kg/min\n")
    print(f"===================================================================")
    
    print(f"Final Coolant flow rate base T = 400:            {qc_history[-1]} kg/min")
    print(f"Final Concentration base T = 400:               {states[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp base T = 400:                {states[-1, 1]:.5f} K")
    print(f"Final Jacket Temp base T = 400:               {states[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states[:,1].min():.5f} K, Max = {states[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {qc_history.min(axis=0):.5f} kg/min, Max = {qc_history.max(axis=0):.5f} kg/min")
    
    print(f"===================================================================")
    print(f"Final Coolant flow rate B case T+2K:     {qc_history_b[-1]} kg/min")
    print(f"Final Concentration B case T+2K:         {states_b[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp B case T+2K:          {states_b[-1, 1]:.5f} K")
    print(f"Final Jacket Temp B case T+2K:           {states_b[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states_b[:,1].min():.5f} K, Max = {states_b[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {qc_history_b.min(axis=0):.5f} kg/min, Max = {qc_history_b.max(axis=0):.5f} kg/min")
    
    print(f"===================================================================")
    print(f"Final Coolant flow rate C case T-10K:     {qc_history_c[-1]} kg/min")
    print(f"Final Concentration C case T-10K:         {states_c[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp C case T-10K:          {states_c[-1, 1]:.5f} K")
    print(f"Final Jacket Temp C case T-10K:           {states_c[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states_c[:,1].min():.5f} K, Max = {states_c[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {qc_history_c.min(axis=0):.5f} kg/min, Max = {qc_history_c.max(axis=0):.5f} kg/min")
    
    print(f"===================================================================")
    print(f"Final Coolant flow rate D case T=475K:     {qc_history_d[-1]} kg/min")
    print(f"Final Concentration D case T=475K:         {states_d[-1, 0]:.5f} mol/m^3")
    print(f"Final Reactor Temp D case T=475K:          {states_d[-1, 1]:.5f} K")
    print(f"Final Jacket Temp D case T=475K:           {states_d[-1, 2]:.5f} K")
    print(f"Temperature: Min = {states_d[:,1].min():.5f} K, Max = {states_d[:,1].max():.5f} K")
    print(f"Coolant Flow Rate: Min = {qc_history_d.min(axis=0):.5f} kg/min, Max = {qc_history_d.max(axis=0):.5f} kg/min")
    print(f"===================================================================")'''

