# Week 3 — the reactor

Started: October 14th 2026

## What I built
non-adiabatic, non-isothermal CSTR with cooling jacket with internal coils using cooling water. Coolant mass flow is manipulated to keep reactor operating temperature at T = 400k. Will build a PI controller.
## What broke, and what fixed it
UA was set to 1000 W/k which didnt make sense it was impossible. Changed it to 10,000 W/K. Lots of problems with making sure units were consistent throughout. Had problems with kWatts and Watts. The heat removal and generation plots were not graphing correctly. diagnosed a units problem in the code and realiazed I was calculating the coolant temperature from an array of 500 elements. Fixed temperature at 400 and collected constants at T = 400 K to obatin the coorect coolant temperature and made sure I was using the reference temperature for the arrenhius equation instead of the feed temperature. Made changes to the model as i went: changed model from fixing the fractional conversion to fixing reactor temperature, checked jacket area size for the conductance value and realized cooling coils were needed for that value of UA, 1. if space-time is fixed then conversion is fixed 2. if target conversion is fixed then reactor space time and vessel volume is fixed for a given v0 3. if reactor Temperature is fixed then botht he heat generation terms and heat removal terms are known constants.
differentiated the heat removal term by keeping Tc constant. Then differentiated the heat removal term with mc constant (mass flow rate of coolant). There was a difference of about 20% bwetween the two numbers. The differentiation with keeping cooolant flow rate constant was much more involved than i initially thought. My numbers and claude's numbers didnt line up on the dQremoved/dT|mc=constant.typed UA = 60000,0 intead of a . python takes that as a 2 member array. after much time finding this bug i typed UA = 6 million instead of 600k. I couldnt figure out why the Tc almost equaled T for the longest time and went through each individual calculation by hand. finally created temp variables to track down individual calculations and realized UA was 6 million in the code. has to be a better way to write zeros. Used the wrong Cp in the heat removal function on pen and paper and it kept leading to a mismatch with code by a small margin which i attributed to rounding error but claude looked through the math and found exactly where in the function i was using the wrong Cp (coolant instead of feed). In the code everything was right
<!-- The most valuable section. Every bug you diagnose is a story you can
     tell in an interview. Root cause, not just symptom. -->

## What I did not understand at first
how distubrances and faults are classified. slope stability criterion. Van Heerden Thermal Multiplicity Diagram. sigmoidal functions. Bifurcation & Hysteresis Loop Diagram
## Decisions I made, and why
derive various cstr analytical soultions first. Used 400K because thats what the plan called for and gemni gave me the parapmeters for the rest of the CSTR.do all algebra on paper first. do a numerical analysis on paper using T = 400K for sanity check on parameters and units. Write code to calculate parameters and heat terms and plot them using a 500 element temperature array. Check plots for steady state and sanity check.converted everything to /minute instead of /second to give the tau (space-time) check more time for faults and fowling. built removal functions for keeping both Tc and mc constant.
<!-- Every arbitrary-looking choice needs its reason recorded NOW, while
     you still have it. "Why 400 K?" is only answerable in week 6 if you
     wrote it down in week 3. -->

## Interview gate — answered out loud, no notes

- [ ] Why does this reactor have three steady states? Which one are you
      on, and how do you know? every intersection between the heat generation function and heat removal function is a steady state location. there are three intersections for this reactor. For T = 400K the two functions intersect at the upper branch which is an ignited steady state branch betwen the dQ_removed/dT > dQ_gen/dT terms. Generation is sigmoidal because the exponential Arrhenius rise is eventually capped by reactant depletion. A 156 K adiabatic rise makes the S steep enough to cross the line three times. 79% conversion implies we are on the top ignited steady state branch, and the slope criterion holds both ways (24.32 > 19.60 with Tc or mc fixed).
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


<!-- Required by check.py stage 3. Write out the three balances and how
     you solved them: component A gives Ca, reactor energy gives Tc,
     jacket energy gives qc. Show the numbers for your operating point. -->

## Van Heerden stability check

| Quantity | Value, J/(L min K) |
|---|---|
| dQgen/dT |        19.597 kW/k |
| dQremoved/dT |    24.33 kW/k  |
| Stable? |yes, dQremoved/dT > dQgen/dT |

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
