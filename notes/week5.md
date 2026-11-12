# Week 5 — detection

Started: November 9 2026

## What I built
monitoring detector that simulates a DCS with an alarm that latchs after consecutive exceedences. False alaram rate set to 1 per day while scanning 
8 tags and any of the 8 tags can trigger an alarm on 2 minute logging interval.


## What broke, and what fixed it
Everything. I had to learn most of the python and math from scratch invluding 
input parameters and how to turn an UCL and LCL into a single scaler. Do not
pad or drop the first w-1 steps. The persistence rule do not have edge effects from a steady state start with drift starting. Sample 0 is valid for faults. Did a per sample  statistic with each tags z aginst a fixed limit. Do not run the alarm on a whole csv as one array, alarm runs on earch run_id seperately. A missiing or frozen sample would need a rule inside a streak. The latch can not come on before onset + (w -1) samples. Did not fully understand statistic window and how and when to corretly align data with loop.

<!-- The most valuable section. Every bug you diagnose is a story you can
     tell in an interview. Root cause, not just symptom. -->

## What I did not understand at first
how to pass csv files and run_ID into a function. How to evaulate individual tags. how to setup the UCL and LCL into a single scaler. How to pass the entire
8 tags into an evaluation where any tag can trigger alarm and that would latch the entire run. 

## Decisions I made, and why
1 false alaram per day. 14 days with the 2 hour warmup. 20 runs over 14 days gives enough samples for training and validation. Each tag has its own streak. Alarm when any one tag stays out for w samples in a row. The 8 latched arrays are combined with a logical OR, which switches on at the earliest latch time so the combined array is still latched. DCS alarm features: a HI/LO limit on all 8 tags, with on-delay condition which a persistence w satisfies. Latching simulates alarm staying on until operator acknowledges it. Real DCS limits are usually set from operating experience or equipment ratings not statistics. A bonferroni-corrected baseline is already better than a typic DCS, with tight limits of = mean ± 3.7546·σ from val, Bonferroni-corrected, same-tag on-delay, tuned to 1 false alaram per day. The future PCA win has to come from using relationships between tags, not just from tighter limits however. Univariate baseline was built with no padding and no NaNs. Each per-sample |z| was passed to to alarms(), ran per run_id, and the counter written in the value > threshold form.
<!-- Every arbitrary-looking choice needs its reason recorded NOW, while
     you still have it. "Why 400 K?" is only answerable in week 6 if you
     wrote it down in week 3. -->

## Interview gate — answered out loud, no notes

- [ ] Explain T-squared and Q to someone non-technical. What is each for?
- [ ] Why is accuracy not in your results table?
- [ ] Your false alarm rate is X%. How confident are you in that number,
      and what would make you more confident?

## Results

| Method | Detection rate | False alarms | Median delay |
|---|---|---|---|
| Univariate | | | |
| PCA | | | |

## Component count

<!-- How many did you keep, by what rule, and why? Record your reasoning
     even if you are unsure. There is a trap in this decision. -->

## Sanity checks passed

- [ ] All components retained gives ~zero residual Q
- [ ] Loadings orthonormal
- [ ] Thresholds fitted on validation ONLY

## Time spent

| Day | Hours | On what |
|---|---|---|
| Mon | | |
| Tue | | |
| Wed | | |
| Thu | | |
| Fri | | |
| Sat | | |
