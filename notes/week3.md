# Week 3 — the reactor

Started: October 14th 2026

## What I built
non-adiabatic, non-isothermal CSTR with cooling jacket with internal coils using cooling water. Coolant mass flow is manipulated to keep reactor operating temperature at T = 400k. Will build a PI controller.
## What broke, and what fixed it
UA was set to 1000 W/k which didnt make sense it was impossible. Changed it to 10,000 W/K. Lots of problems with making sure units were consistent throughout. Had problems with kWatts and Watts. The heat removal and generation plots were not graphing correctly. diagnosed a units problem in the code and realiazed I was calculating the coolant temperature from an array of 500 elements. Fixed temperature at 400 and collected constants at T = 400 K to obatin the coorect coolant temperature and made sure I was using the reference temperature for the arrenhius equation instead of the feed temperature. Made changes to the model as i went: changed model from fixing the fractional conversion to fixing reactor temperature, checked jacket area size for the conductance value and realized cooling coils were needed for that value of UA, 1. if space-time is fixed then conversion is fixed 2. if target conversion is fixed then reactor space time and vessel volume is fixed for a given v0 3. if reactor Temperature is fixed then botht he heat generation terms and heat removal terms are known constants.
differentiated the heat removal term by keeping Tc constant. Then differentiated the heat removal term with mc constant (mass flow rate of coolant). There was a difference of about 20% bwetween the two numbers. The differentiation with keeping cooolant flow rate constant was much more involved than i initially thought. My numbers and claude's numbers didnt line up on the dQremoved/dT|mc=constant.typed UA = 60000,0 intead of a . python takes that as a 2 member array. after much time finding this bug i typed UA = 6 million instead of 600k. I couldnt figure out why the Tc almost equaled T for the longest time and went through each individual calculation by hand. finally created temp variables to track down individual calculations and realized UA was 6 million in the code. has to be a better way to write zeros. Used the wrong Cp in the heat removal function on pen and paper and it kept leading to a mismatch with code by a small margin which i attributed to rounding error but claude looked through the math and found exactly where in the function i was using the wrong Cp (coolant instead of feed). In the code everything was right. set deltaH to 25,000 instead of 250,000, nothing would have crashed but the results would have no three steady states or a van heerden check. the heat generation sigmodial part would have flatened. do not put derived quantities in the parameter definition fields. they can not be replaced. learned how to use p = default_params() correctly and how to pass p into functions. 
<!-- The most valuable section. Every bug you diagnose is a story you can
     tell in an interview. Root cause, not just symptom. -->

## What I did not understand at first
how distubrances and faults are classified. slope stability criterion. Van Heerden Thermal Multiplicity Diagram. sigmoidal functions. Bifurcation & Hysteresis Loop Diagram. control loop and coolant residence time calculations

## Decisions I made, and why
derive various cstr analytical soultions first. Used 400K because thats what the plan called for and gemni gave me the parapmeters for testing the rest of the CSTR (checked if these made sense using cooling water as coolant).did all algebra on paper first. do a numerical analysis on paper using T = 400K for sanity check on parameters and units. Write functions to calculate steady-state parameters and heat terms and plot them using a 500 element temperature array. Check plots for steady state and sanity check.converted everything to /minute instead of /second to give the tau (space-time) check (in check.py) more time for faults and fowling. built removal functions for keeping both Tc and mc constant.rewrote everything into cstr.py to conform with check.py. looked into different cooling jacket geometries (using steady state mc) including using annular jacket volume with a inner jacket wall set to 0.050m (high space-time), using coils directly inside the reactor (lowest spacetime), and using half-pipe flow weilded directly to reactor surface and bottom head (middle spacetime). decided on the half-pipe flow because its a resonable design decision with a spacetime of 1.1 minutes. the variable coolant flow rate can be passed directly into the deriviatives with the required coolant volume in the half pipes. the manipulated variable is coolant flow rate and the hold up is the mass of coolant in the half pipes
<!-- Every arbitrary-looking choice needs its reason recorded NOW, while
     you still have it. "Why 400 K?" is only answerable in week 6 if you
     wrote it down in week 3. -->

## Interview gate — answered out loud, no notes

- [ ] Why does this reactor have three steady states? Which one are you
      on, and how do you know? ANS: every intersection between the heat generation function and heat removal function is a steady state location. there are three intersections for this reactor. For T = 400K the two functions intersect at the upper branch which is an ignited steady state branch where dQ_removed/dT > dQ_gen/dT terms. Generation is sigmoidal because the exponential Arrhenius rise is eventually capped by reactant depletion. the generation function reaches maximum when conversion reaches 1, all of the reactant is already gone so the reactor cant generate any more heat. A 156 K adiabatic rise makes the S steep enough to cross the line three times. 79% conversion implies we are on the top ignited steady state branch,
- [ ] Where does the fouling fault show up, and where does it NOT? Why?
- [ ] What is integral windup, and what did you do about it?

## Steady-state algebra
tau = V/v0
Xa = (k(400)*tau)/(1+k(400)*tau)        #fractional conversion
k = k_ref*exp((Ea/R)*(1/T_ref - 1/T))   #arrenhius relation
Ca = Ca0*(1-Xa)                         #exit concentration
Fa0,Fa = v0*Ca0, v0*Ca                  #definitions

mass balance: Fa0 - Fa + ra*V = 0
reactor energy balance: p*v0*Cp*(T0-T) + (-deltHrxn)*(-ra*V) - UA*(T - Ta) = 0
jacket energy balance: UA*(T - Ta) = mc*Cpc*(Ta - Tc,in)
Qinlet + Qgen - Qjacket = 0
numerical values are in Heat_plots.py

Coolant at 80.7 °C	It goes to a heat exchanger and the fouling fault becomes a process-side deposits on the coils, which is plausible for a reactor this hot. 
ΔH = 250 kJ/mol	Deliberately high, to create multiplicity in operating conditions including the adiabatic temperture rise

<!-- Required by check.py stage 3. Write out the three balances and how
     you solved them: component A gives Ca, reactor energy gives Tc,
     jacket energy gives qc. Show the numbers for your operating point. -->

## Van Heerden stability check

| Quantity | Value, kW/K        |
|---|---|
| dQgen/dT |        19.597 kW/K |
| dQremoved/dT |    24.32 kW/K  |
| Stable? |yes, dQremoved/dT > dQgen/dT |


Removal assumption	      Low	       Middle       Operating	   deltaT unstable state
Tc held fixed (blue)	337.3 K	 354.3 K	       400 K	          46 K
Coolant flow held fixed 	302.5 K	 382.6 K	       400 K	          17 K

Question 3: With the coolant valve froze at its steady state value, which is what “open loop” means for this reactor: (a) at T = 400k the reactor stays at 400k as removal = generation (b) at T = 402 the reactor recovers to 400K as removal > generation (c) at T = 390K the reactor recovers to 400k as generation is > than removal (d) the reactor approaches 400k as generation is still > than removal and we are still above the unstable middle at 383.6 K. It would take a  17 K dip in reactor temperature to cross the unstable middle state with the coolant valve frozen open. From there the reactor falls to the extinguished steady state near 302 K and conversion collapses.


d(Q_jacket)/dT = dQgen/dT − ρ·v0·Cp_feed = 19.60 − 20.00 = −0.40 kW/K

	Margin (removal slope − generation slope)
Feed alone (dQfeed/dT)	20.00 − 19.60 = 0.40 kW/K 
Feed + jacket[coolant flow fixed (dQremoved/dT)]	24.32 − 19.60 = 4.72 kW/K
The feed does most of the heat removal. The jacket provides almost all of the stability.




## Time spent

| Day | Hours Oct        | On what |
|---|---|---|
| Mon | |  |             analytical CSTR nonisothermal+nonadiabatic at steady state
| Tue | | 2|   14th           "
| Wed | | 2|                  "
| Thu | | 2|                  "
| Fri | | 2|                  "
| Sat | | 2|                  "
Sun       2                   "
Mon       2    19th           "
Tues      4    20th      coding, math, plots, cleanup
wed       4              dynamic cstr
thur      4              math clean up 
frid      4              code clean up
sat       4    24        dynamic cstr
