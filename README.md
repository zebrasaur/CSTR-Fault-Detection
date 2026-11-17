This project aims to detect faults (fouling, pump loss, drift) on a 
jacketed CSTR under PI temperature controller acting on coolant flowrate
![Money plot](../figures/money_plot.png)

Work in progress: week 5 of 6. Detection results pending.

Typical controllers hide faults affecting reactor temperature (as shown in the money_plot) and this project aims to correlate multiple reactor variables to be able tell when a hidden fault (such as fouling) occurs.

I wrote all physics, control, fault and detection code. I used Claude as a reviewer: it checked derivations, reran results independently, and caught bugs, which are documented in the notes.

PLAN.md and check.py are the project’s self-imposed plan and acceptance tests.

```
PLAN.md      the six-week plan 
check.py     automated acceptance checks; the specification
src/         model, controller, faults, data generation, monitoring
analysis/    scripts and figures
tests/       pytest
notes/       one markdown file per week 
data/        generated in week 4, not committed
results/     generated in week 5
figures/     generated in weeks 4-6
```

## How the checker works

python check.py       #check.py is the acceptance test for each stage
python check.py 3         
python check.py 3 --spec   

The checks test behaviour and invariants, never implementation. There are
many correct ways to pass them. When one fails it tells you what is wrong
and usually why, the failure messages are the most useful thing in this
folder, so read them properly rather than skimming 

Some things the checker cannot verify. Those stages print a manual
checklist instead. Do not skip them because nothing enforces them; the
fouling fault behaving correctly is not machine-checkable and is also the
entire point of the project.

