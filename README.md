# Start here

You are building a chemical process fault-detection system from scratch,
in six weeks, at roughly 20 hours a week. This folder is the scaffolding.
It contains no solutions.

```
PLAN.md      the six-week plan -- read this first, all of it
check.py     automated acceptance checks; the specification
src/         your code goes here (empty)
notes/       one markdown file per week (start week1.md on day one)
data/        generated in week 4, not committed
results/     generated in week 5
figures/     generated in weeks 4-6
```

## Day one, in order

1. Read `PLAN.md` end to end. It is long; read it anyway. Twenty minutes
   now saves a wasted week later.
2. Install Python 3.11+, git, and an editor.
3. Create the GitHub repo and clone it.
4. `python check.py` — everything fails. That is the correct starting
   state.
5. `python check.py 1 --spec` — this is your first task.
6. Open `notes/week1.md` and write the date.

## How the checker works

```bash
python check.py            # progress across all stages
python check.py 3          # detailed results for stage 3
python check.py 3 --spec   # the interface stage 3 expects
```

The checks test behaviour and invariants, never implementation. There are
many correct ways to pass them. When one fails it tells you what is wrong
and usually why — the failure messages are the most useful thing in this
folder, so read them properly rather than skimming for red.

Some things the checker cannot verify. Those stages print a manual
checklist instead. Do not skip them because nothing enforces them; the
fouling fault behaving correctly is not machine-checkable and is also the
entire point of the project.

## The deal

I will not show you my implementation until you finish week 6. Ask me
for anything else: concepts, debugging, code review, why your reactor is
diverging, what a virtual environment actually is, whether your README
reads well. Ask early and often — the 45-minute rule in `PLAN.md` is
there because grinding is not learning.

The reference implementation is sitting in `../cstr-fault-detection/`.
Move it somewhere inconvenient, or agree with yourself not to open it.
If you read it now you will absorb my decisions instead of making your
own, and the finished repo will not be defensible in a room.

## What "done" looks like

A public repo where you can be asked about any line and answer without
hesitating, with a README whose most interesting section is the one about
what did not work — and a ten-minute verbal walkthrough you can give
cold.

That is the deliverable. The code is just how you get there.
