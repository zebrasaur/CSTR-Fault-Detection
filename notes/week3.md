# Week 3 — the reactor

Started: October 14th 2026

## What I built
non-adiabatic, non-isothermal CSTR with cooling jacket with internal coils using cooling water. Coolant mass flow rate is manipulated to keep reactor operating temperature at the steady state operating Temperture. Built a PI controller, tunning based on a first order plus dead time model, acting on the coolant mass flow rate and tuned using step-testing runs on varying coolant flow rates at Temperature T = 400K. Added sensor noise, T, Tc, Ca, qc, to the controller. Added fault injection to the reactor.

## What broke, and what fixed it
UA was set to 1000 W/k which didnt make sense it was impossible. Changed it to 10,000 W/K. Lots of problems with making sure units were consistent throughout. Had problems with kWatts and Watts. 

The heat removal and generation plots were not graphing correctly. diagnosed a units problem in the code and realiazed I was calculating the coolant temperature from an array of 500 elements. Fixed temperature at 400 and collected constants at T = 400 K to obatin the coorect coolant temperature and made sure I was using the reference temperature for the arrenhius equation instead of the feed temperature. 

Made changes to the model as i went: changed model from fixing the fractional conversion to fixing reactor temperature, checked jacket area size for the conductance value and realized cooling coils were needed for that value of UA, 1. if space-time is fixed then conversion is fixed 2. if target conversion is fixed then reactor space time and vessel volume is fixed for a given v0 3. if reactor Temperature is fixed then both the heat generation terms and heat removal terms are known constants.

differentiated the heat removal term by keeping Tc constant. Then differentiated the heat removal term with mc constant (mass flow rate of coolant). There was a difference of about 20% bwetween the two numbers. The differentiation with keeping cooolant flow rate constant was much more involved than i initially thought. My numbers and claude's numbers didnt line up on the dQremoved/dT|mc=constant.

typed UA = 60000,0 intead of a . python takes that as a 2 member array. after much time finding this bug i typed UA = 6 million instead of 600k. I couldnt figure out why the Tc almost equaled T for the longest time and went through each individual calculation by hand. finally created temp variables to track down individual calculations and realized UA was 6 million in the code. has to be a better way to write zeros. 

Used the wrong Cp in the heat removal function on pen and paper and it kept leading to a mismatch with code by a small margin which i attributed to rounding error but claude looked through the math and found exactly where in the function i was using the wrong Cp (coolant instead of feed). In the code everything was right. 

I only had one steady state intersection near 300k. Causes: a mix of watts and kWatts. An array-scalar mismatch in Q_gen_400 (using CA array and XA array) in trying to calculate the scalar Qgen at T=400k. And a sign error in calculating the jacket heat term from the jacket energy balance.

I set deltaH to 25,000 instead of 250,000, nothing would have crashed but the results would have no three steady states or a van heerden check. the heat generation sigmodial part would have flatened. do not put derived quantities in the parameter definition fields. they can not be replaced. 

learned how to use p = default_params() correctly and how to pass p into functions. check.py has specific variable names it looks for and specific signature field that has to match otherwise you will get fail messages even though the code is correct. 

lots of bugs plotting the dynamic results. ran into a wierd bug where brackets in the output line on a display character caused plotlib to crash, causes was a bracket i deleted and had to put back in. still not clear why a bracket in a comment string would cause a crash. fixed line widths and colors, legend, display bugs and learned to write 2 plots in one.

Designed high temperature reactor start into open_loop and plot outputted an oscillation at low time. first thought was turning poiits in the removal terms. Claude pointed out that those curves are steadystate and not dependent on time and suggested these oscillations might be numercial and ran tests halving the step size dt. at low dt<0.05 the system stablized (system stiffness is C_A eignvalue which is 1/tau) from a hot start. A step size should always be justified across the whole range of temperatures a system could operate in. 

Realized tuned controller was only good for the range of temperatures around the target temperature. For
T = 400K, the tunning paramters are only good for Temperatures 355K - 448K. Temperatures outside of that
range require controller retune as well as a full stability check. Temperatures outside of those ranges also produce negative coolant flow rates which i flaged as an errror message output. 

Codded sensor noise function into invidual state parameters, temperatures, concentrations and coolant flow rate. then decided to code the noise directly into the 2D numpy array. realized the temperature noise was also fed to the controller. redid the noise function for each indivdual paramter.

<!-- The most valuable section. Every bug you diagnose is a story you can
     tell in an interview. Root cause, not just symptom. -->

## What I did not understand at first
how distubrances and faults are classified. slope stability criterion. Van Heerden Thermal Multiplicity Diagram. sigmoidal functions. control loop and coolant residence time calculations

My steady-state stability analysis said 17 K of margin to reactor death. Simulation showed dips larger than 5.2 K  would extinguish the reactor with the valve frozen, because the diagram assumes concentration has already settled at the new temperature while my simulation used the concentration value at T = 400k, the steady state value, this produced a generation term that was 25% below the van heerden diagram. As T falls, generation falls and CA can't refill fast enough to recover.

Test results
Starting state at T = 390 K, valve frozen	    |      Final T
==============================================================================
C_A = 530.75 (the 400 K value), original case (c)|    302.45 K, extinguished
C_A = 709.09 (settled at 390 K), Tc at the 400 K |    400.00 K, recovers
C_A = 709.09, Tc = 348.16  also settled at 390 K |    400.00 K, recovers

reactant deficit, not the temperature caused the extinction is prior cases

Feed temperature step	          Final T
===============================================================================
     −5 K	                    297.3 K, extinguished
     −10 K	               292.5 K, extinguished
     −20 K	               283.3 K, extinguished
The deeper finding: reactor operating point sits near the “nose”. the heat curves are almost nearly tangent

Feed-temperature drop that eliminates the ignited steady state, valve frozen	1.04 K

with coolant flow at zero, removal is only the feed flow term, so it can absorb feed drops of up to about 23 K (from 2,462 kW = 20 kW/K × (400 − T0), T0 ≥ 276.9 K). So 1 K open-loop reactor becomes about 23 K closed-loop reactor. running at 400 K with these parameters leaves almost no open-loop margin and the controller must handle all pertubations to keep stability. 

The highest temperature an uncooled CSTR can sustain is bounded by T0 + deltaT_ad, because generation 
saturates at full conversion while the feed’s sensible duty keeps rising. With T0 = 300, deltaT_ad = 156.25K, Tmax = 456.25, the conversion at this temp is X = 0.95 using our residence time vo/V, the actual 
Temperature is lower, 448 K in my case.


## Decisions I made, and why
derive various cstr analytical soultions first. Used 400K because thats what the plan called for and gemni gave me the parapmeters for testing the rest of the CSTR (checked if these made sense using cooling water as coolant).did all algebra on paper first. do a numerical analysis on paper using T = 400K for sanity check on parameters and units. Write functions to calculate steady-state parameters and heat terms and plot them using a 500 element temperature array. 

Check plots for steady state and sanity check.converted everything to /minute instead of /second to give the tau (space-time) check (in check.py) more time for faults and fowling. built removal functions for keeping both Tc and mc constant.rewrote everything into cstr.py to conform with check.py. looked into different cooling jacket geometries (using steady state mc) including using annular jacket volume with a inner jacket wall set to 0.050m (high space-time), using coils directly inside the reactor (lowest spacetime), and using half-pipe flow weilded directly to reactor surface and bottom head (middle spacetime). 

Decided on the half-pipe flow because its a resonable design decision with a spacetime of 1.1 minutes. the variable coolant flow rate can be passed directly into the deriviatives with the required coolant volume in the half pipes. the manipulated variable is coolant flow rate and the hold up is the mass of coolant in the half pipes

Sigma errors: for temperature senors, modeled after Pt100RTD sensors with T_simga = 0.03 (high accuracy). For the coolant flow rate (flow_frac) sigma was modeled after a electromagnatic meter (magmeter) with flow_frac = 0.02. The concentration analysis was done using "state estimators" with soft sensors using state parameters. For our reactor, T, Tc, qc and default paramters are used to calculate Ca_measured = Ca + noise, with simga_Ca = 0.03.

Fluid feed properties are water like with rho 1000 kg/m^3 and Cp = 4000 j/kg*K. to avoid a gas phase, the
reactor is kept pressurized at 2.5 bar absolute for T = 400k. vapor pressure and venting not modelled. liquid is assumed throughout including exit stream (effluent throttling ) via control valve (not modelled). Constant volume of liquid held by nitrogen padding of the reactor vapor headspace with back pressure regulation and effluent throttling. 



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

Question 3: With the coolant valve froze at its steady state value, which is what “open loop” means for this reactor: (a) at T = 400k the reactor stays at 400k as removal = generation (b) at T = 402 the reactor recovers to 400K as removal > generation (c) at T = 390K the reactor recovers to 400k as generation is > than removal (d) the reactor approaches 400k as generation is still > than removal and we are still above the unstable middle at 382.6 K. It would take a  17 K dip in reactor temperature to cross the unstable middle state with the coolant valve frozen open. From there the reactor falls to the extinguished steady state near 302 K and conversion collapses.


d(Q_jacket)/dT = dQgen/dT − ρ·v0·Cp_feed = 19.60 − 20.00 = −0.40 kW/K

	Margin (removal slope − generation slope(19.6))
Feed alone:	20.00 − 19.60 = 0.40 kW/K 
Feed + jacket[coolant flow fixed]:	24.32 − 19.60 = 4.72 kW/K
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
