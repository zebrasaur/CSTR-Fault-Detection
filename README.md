Work in progress: week 5 of 6. Detection results pending.

I wrote all physics, control, fault and detection code. I used Claude as a reviewer: it checked derivations, reran results independently, and caught bugs, which are documented in the notes

PLAN.md and check.py are the project’s self-imposed plan and acceptance tests.

```
PLAN.md      the six-week plan 
check.py     automated acceptance checks; the specification
src/          code goes here (empty)
notes/       one markdown file per week 
data/        generated in week 4, not committed
results/     generated in week 5
figures/     generated in weeks 4-6
```

## Day one, in order

1. Read `PLAN.md` end to end
2. Install Python 3.11+, git, and an editor.
3. Create the GitHub repo and clone it.
4. `python check.py` — everything fails. That is the correct starting
   state.
5. `python check.py 1 --spec`  week 1 specs
6. Open `notes/week1.md` and write the date.

## How the checker works

```bash
python check.py            # progress across all stages
python check.py 3          # detailed results for stage 3
python check.py 3 --spec   # the interface stage 3 expects
```

The checks test behaviour and invariants, never implementation. There are
many correct ways to pass them. When one fails it tells you what is wrong
and usually why, the failure messages are the most useful thing in this
folder, so read them properly rather than skimming 

Some things the checker cannot verify. Those stages print a manual
checklist instead. Do not skip them because nothing enforces them; the
fouling fault behaving correctly is not machine-checkable and is also the
entire point of the project.

