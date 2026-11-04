# Week 4 — dataset and splits

Started: <date>

## What I built

## What broke, and what fixed it

<!-- The most valuable section. Every bug you diagnose is a story you can
     tell in an interview. Root cause, not just symptom. -->

## What I did not understand at first

## Decisions I made, and why
240 total runs: 14 days plus a 2 h warm-up(discarded, needed for drift), drift on, fault start randomly drawn between day 2 and day 5, data logged every 2 minutes to 4 decimal places, with measured data and truth channels in separate files. Fouling: 10-50% UA loss, 3-day ramp. Pump loss: 10-70% flow loss, step. RTD bias: 0.5-5k, random sign, step. All faults randomly start between day 2 to day 7. All faults last to day 14. 

<!-- Every arbitrary-looking choice needs its reason recorded NOW, while
     you still have it. "Why 400 K?" is only answerable in week 6 if you
     wrote it down in week 3. -->

## Interview gate — answered out loud, no notes

- [ ] Why three splits and not two?
- [ ] Your dataset is simulated. What does that mean your results do and
      do not demonstrate?

## Split design
Split	     Runs	     Contents	          Seeds
Train	     20	     Normal	          0–19
Validation	20	     Normal	          1000–1019
Test	          200	     50 normal; 
                         50 fouling,    
                         50 pump loss, 
                         50 RTD bias	     2000–2199

Fault	     Severity	     Shape           Type
Fouling	     10–50%         UA loss	     3-day ramp
Pump loss	     10–70%         flow loss	     Step
RTD bias	     0.5–5 K        random sign	Step

## The money plot

<!-- Once healthy vs fouling is plotted: does reactor temperature really
     look identical? By how much does coolant flow diverge? This figure
     opens your README, so describe what it shows in one sentence. -->

## Time spent

| Day Nov Hours | On what |
|---|---|---|
| Mon   |   |
| Tue 3 | 4 |    setup, parameters        
| Wed   |   |
| Thu   |   |
| Fri   |   |
| Sat   |   |
