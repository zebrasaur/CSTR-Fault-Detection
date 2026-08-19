# Build it yourself: 6 weeks, ~130 hours

A staged plan to build the CSTR fault-detection project from zero, where
"zero" means Python mechanics, numpy/pandas, and git. Not statistics.

---

## The honest assessment

**This is achievable in 6 weeks, and it would not be for most people.**
The reason is specific and worth internalising, because it is also your
pitch to an employer.

A typical career-changer attempting this project is learning three things
at once: the programming, the statistics, and the process engineering.
They usually stall on the third, because you cannot fake knowing what a
heat exchanger fouling actually does to a control loop, and without that
the project becomes "I ran PCA on some numbers."

You are learning **one** of the three. Break the work down:

| Component | Your status |
|---|---|
| Reactor design, mass/energy balances, operating point selection | You have an MS in this |
| Why a controller masks a fault; what an operator would actually see | 20 years of it |
| PCA, distributions, thresholds, cross-validation, overfitting | You said not-zero |
| Python, numpy, pandas, git | **This is the actual gap** |

So the plan front-loads tooling and then lets you spend most of the six
weeks in territory you already know, expressed in a language you are
still learning. That is a much easier problem than it looks from here.

**Where it could go wrong:** weeks 5 and 6. If you are behind schedule,
that is where it will show. There is a defined cut line below — take it
without guilt if you need it. A smaller repo you fully understand beats a
larger one you do not, and the whole point of doing this yourself is that
the difference is visible in about ninety seconds of conversation.

---

## The rules

1. **You write every line.** I will not show you my implementation until
   week 6. I will answer questions, review your code, explain concepts,
   and debug with you — but I will not hand you the function.
2. **`python check.py N` is the spec.** Each stage has automated
   acceptance checks. Green means you built the right thing. It does not
   mean you built it well; that is what code review is for, and you
   should ask me for one at the end of each stage.
3. **Commit every working day.** Not for the portfolio — for the habit,
   and because your commit history is evidence of how you work.
4. **Keep a `notes/` folder.** One markdown file per week: what broke,
   what you tried, what you concluded. This becomes the raw material for
   the README and for interview answers, and you will not remember any
   of it in week 6 if you do not write it down.
5. **If you are stuck for more than 45 minutes, ask.** Struggle is where
   learning happens, right up until it becomes grinding, and past that
   point you are just losing hours.

---

## Cut lines

If you fall behind, ship the smaller thing. In descending order of value:

- **Must have (weeks 1–5).** Simulator, dataset with clean splits, PCA
  monitoring, honest metrics, README. This alone is a strong repo.
- **Should have (week 6).** Dynamic PCA. This is the single most
  interesting technical result in the project.
- **Nice to have.** Supervised diagnosis, hyperparameter sensitivity,
  root-cause attribution.

Drop from the bottom. Never drop the honest metrics to buy a feature —
the metrics *are* the project.

---

# Week 1 — Tooling (~22 hrs)

The only week with no chemical engineering in it. Get through it fast;
it is the least interesting part and everything after depends on it.

### Goal
Working Python environment, a public GitHub repo, and enough Python to
write a function without looking everything up.

### What's new
Everything: the interpreter, virtual environments, `pip`, imports,
running a script from a terminal, git.

### Build

Set up first:
- Python 3.11+, VS Code (or your editor of choice), git
- A virtual environment. Learn what it is and why it exists — this
  confuses everyone at first and then never again.
- A GitHub repo named something like `cstr-fault-detection`, cloned
  locally, with a README that says one sentence about the project.

Then write `src/warmup.py` containing three functions. These are not
throwaway exercises — you will reuse the third one in week 5.

```python
def moving_average(values, window):
    """Return a list of averages over each consecutive `window` values.
    Result is shorter than the input by (window - 1)."""

def standardize(values):
    """Return values as (x - mean) / standard_deviation, as a list.
    Use the sample standard deviation (divide by n-1)."""

def count_consecutive_above(values, threshold, n):
    """Return True if at least `n` consecutive values exceed `threshold`."""
```

Write all three in **pure Python** — loops and lists, no numpy. You are
learning the language, and in week 2 you will rewrite two of them in one
line of numpy each, which is the fastest way to understand what numpy is
actually for.

### Acceptance
```bash
python check.py 1
```

### Interview gate
Be able to answer, out loud, without notes:
- What is a virtual environment and what problem does it solve?
- What is the difference between a list and a dict, and when do you reach
  for each?
- What does `if __name__ == "__main__":` do and why is it there?

### Resources
- The official Python tutorial at `docs.python.org/3/tutorial/` —
  sections 3 through 5 cover most of what you need.
- The *Pro Git* book at `git-scm.com/book`, chapters 1–3. Ignore
  branching for now; you only need add/commit/push this week.

---

# Week 2 — numpy and an integrator (~22 hrs)

Here your background starts paying. You know what an ODE is and why RK4
beats Euler; you are learning to express it.

### Goal
Rewrite your week-1 functions in numpy, then build a Runge-Kutta
integrator and verify it properly.

### What's new
numpy arrays, vectorized operations, array shapes, slicing. Shapes will
be the source of roughly 80% of your errors for the next month. This is
normal.

### Build

`src/integrate.py`:

```python
def rk4_step(f, y, t, dt):
    """One classical 4th-order Runge-Kutta step.
    f(y, t) returns dy/dt as a numpy array. Returns the new y."""
```

Then verify it three ways, in `src/test_integrate.py` (your own script,
separate from `check.py`):

1. **Against an analytic solution.** Integrate `dy/dt = -k*y` and compare
   to `y0 * exp(-k*t)`.
2. **Convergence order.** Halve `dt` and confirm the error drops by
   roughly 16×. If it drops by 2× you have written Euler's method by
   accident. This test catches more real bugs than any other.
3. **A conserved quantity.** Integrate a harmonic oscillator and check
   the total energy does not drift.

That third test is the habit worth forming: **find a quantity your
system must conserve and check it.** You will use exactly this instinct
in week 3 when you check that your reactor closes its energy balance.

### Acceptance
```bash
python check.py 2
```

### Interview gate
- Why is RK4 fourth-order? What does "order" mean here?
- Your convergence test — why 16× and not 4×?
- What does "vectorized" mean and why is a numpy loop over 100,000
  elements slower than the equivalent array expression?

---

# Week 3 — The reactor (~24 hrs)

The heaviest build week and the one where your degree does the work.

### Goal
A non-isothermal CSTR with a cooling jacket, under PI control, with
injectable faults.

### What's new
Very little conceptually. Mostly: organising a larger program, and
`dataclass` for parameter bundles.

### Build

Work in this order. **Do not skip step 1 to get to the simulation** — if
you cannot solve the steady state on paper, you will not be able to tell
whether your simulator is wrong.

1. **Derive the steady state by hand.** Pick a target reactor
   temperature. Component balance gives you `Ca`. Reactor energy balance
   gives you the required jacket temperature. Jacket energy balance gives
   you the required coolant flow. Write this up in `notes/week3.md` with
   the algebra.

2. **Check open-loop stability** with the van Heerden criterion — compare
   `dQgen/dT` against `dQremoved/dT`. This determines whether your chosen
   operating point is on a stable branch. A CSTR like this has three
   steady states and picking the wrong one will make your simulation
   diverge, which is a genuinely instructive failure if it happens to
   you. It happened when I built this.

3. `src/cstr.py` with:
```python
def derivatives(state, params, ...):
    """Return d/dt of (Ca, T, Tc) as a numpy array."""

def solve_steady_state(T_target, params):
    """Return (Ca, T, Tc, qc, conversion) from the algebra in step 1."""

def stability_margin(T_target, params):
    """Return (dQgen_dT, dQremoved_dT), both per unit volume."""

def simulate(duration, dt, params, controller, fault, ...):
    """Run the reactor. Return a dict of logged arrays."""
```

4. **Add a PI controller** on reactor temperature, manipulating coolant
   flow. Include anti-windup — clamp the integral term when the valve is
   at a limit. Skipping this produces a very specific bug that will
   confuse you for a day.

5. **Add faults**, as a separate object from the physics. The reactor
   should not know faults exist; a fault modifies parameters as the
   simulation runs. Start with fouling (`UA` decays) and coolant supply
   loss (`Tc_in` steps up).

6. **Add measurement noise and slow feed disturbances**, so "normal"
   drifts rather than sitting still. Without this the detection problem
   in week 5 is trivial and the results are meaningless.

### Acceptance
```bash
python check.py 3
```

### Interview gate
- Why does this reactor have three steady states? Which one are you on,
  and how do you know?
- Where does the fouling fault show up, and where does it *not*? Why?
- What is integral windup and what did you do about it?

That second question is the heart of the project. Practise it.

---

# Week 4 — Data and pandas (~20 hrs)

### Goal
Generate a dataset with defensible splits, and see the phenomenon your
project is about.

### What's new
pandas DataFrames, CSV I/O, `groupby`. matplotlib.

### Build

1. `src/generate_data.py` producing three **disjoint** splits of normal
   runs — train, validation, test — plus faulted runs that appear only
   in test. Randomise fault severity across a range.

   Think hard about why validation exists before you write it. If you
   cannot explain why setting thresholds and measuring false alarms on
   the same runs is cheating, stop and work that out first. It is the
   most common flaw in amateur ML portfolios and being able to articulate
   it puts you ahead of a lot of bootcamp graduates.

2. **The money plot.** Overlay a healthy run and a fouling run: reactor
   temperature, coolant flow, jacket temperature, product concentration.
   Temperature should be indistinguishable while coolant flow diverges.

   When you see that plot come out right, you have proven your simulator
   reproduces the real phenomenon. It is also the figure that will open
   your README.

3. Log ground-truth channels (true temperature, true `UA`) separately
   and **never let a detector read them**. You need them to score
   detection delay honestly.

### Acceptance
```bash
python check.py 4
```

### Interview gate
- Why three splits and not two?
- Your dataset is simulated. What does that mean your results do and do
  not demonstrate?

---

# Week 5 — Detection (~24 hrs)

The core result. Budget generously; this is where the concepts you
already have get expressed in code for the first time.

### Goal
Three detectors, scored honestly.

### Build

1. **Univariate baseline.** Independent limits on each tag, alarm if any
   is exceeded. This is what a DCS already does, so it is the honest
   "do nothing new" comparison — and you must Bonferroni-correct the
   per-tag significance or the comparison is rigged.

2. **PCA from scratch, via SVD.** Standardize, take the SVD, keep some
   components. Verify with an identity: if you keep *all* components, the
   reconstruction residual must be ~0. If it is not, your loadings are
   transposed. It is always the transpose.

3. **T² and Q.** T² is distance from centre inside the model subspace; Q
   is the energy left outside it. Q is the one that catches most
   equipment faults, because degradation breaks *relationships* between
   variables rather than pushing one variable out of range.

4. **How many components?** Do not reflexively take 95% of variance.
   Look at the eigenvalue spectrum and decide, then write down your
   reasoning. There is a real trap here that I hit — I will not tell you
   what it is, but if something downstream starts giving suspiciously
   uniform answers, come back to this decision.

5. **Alarm logic.** Reuse `count_consecutive_above` from week 1. A single
   sample over the limit is noise; requiring persistence is what stops
   operators from disabling the system.

6. **Thresholds from validation only.** Empirical quantiles, not the
   textbook F-distribution limits — process data is not multivariate
   normal and you can say so out loud.

7. **Metrics: detection rate, false alarm rate, detection delay.** Not
   accuracy. Work out for yourself why accuracy is useless here before
   you read the next sentence — it is because 99% of operating time is
   normal, so a detector that never alarms scores 99%.

   Put a confidence interval on every rate. With 20 runs per fault type,
   a bare percentage overstates what you know.

### Acceptance
```bash
python check.py 5
```

### Interview gate
- Explain T² and Q to someone non-technical. What is each one *for*?
- Why not accuracy?
- Your false alarm rate is X%. How confident are you in that number, and
  what would make you more confident?

---

# Week 6 — Dynamics, honesty, and shipping (~20 hrs)

### Goal
The best technical result in the project, an honest write-up, and a
published repo.

### Build

1. **Dynamic PCA.** Stack each sample with the previous few samples and
   run the same machinery on the widened matrix. Embed each run
   *separately* — if you concatenate runs before embedding you will
   splice the end of one batch onto the start of the next and invent
   transients that never happened.

   Expect a real improvement, especially on any fault that changes the
   *dynamics* rather than the mean.

2. **Sensitivity sweep.** Vary the number of components and lags, and
   report the range. If your headline number only holds in one cell of
   the grid, it is tuning, not a result. Report it either way.

3. **The README.** Structure it as: the phenomenon, the headline result,
   why the metrics are what they are, **what did not work**, limitations.

   The "what did not work" section is not modesty, it is the strongest
   section in the document. Anyone can report a number that went up.
   Reporting a method you tried, diagnosed as broken, and understood is
   the thing that reads as an engineer rather than a tutorial follower.

4. **Publish.** Push it, check the README renders, check the figures
   load, check a stranger could clone it and run `run_all.sh`.

5. **Then, and only then, ask me to unlock my version.** Compare. Where
   we differ, decide which is better — sometimes yours will be, and
   noticing that is the point.

### Acceptance
```bash
python check.py 6
```

### Interview gate
The full walkthrough, 10 minutes, no notes:
- What problem, and why is it hard?
- What did you build?
- What are the numbers, and what are the error bars?
- What failed, and what did you learn from it?
- What would you do differently with real plant data?

---

## How not to fool yourself

- **The checker passing is not understanding.** After each stage, close
  the file and re-explain your solution out loud. If it does not come,
  reread it — that gap is exactly what an interview exposes.
- **Do not tutorial-hop.** You will be tempted to go find a course when
  a stage gets hard. Six weeks is not enough time for that and you will
  learn more from debugging your own reactor than from watching someone
  else build a to-do app.
- **Copying from me later is self-defeating.** If you get to week 6 and
  ask for my implementation to paste, you will have spent 130 hours to
  end up where you started this conversation.
- **Bugs that produce plausible output are the dangerous ones.** A crash
  tells you something is wrong. A number that is quietly wrong does not.
  This is why every stage has an invariant to check — conservation,
  reconstruction identity, convergence order.

---

## Weekly rhythm

| Day | Focus |
|---|---|
| Mon–Thu | Build. ~4–5 hrs/day. |
| Fri | Run `check.py`, ask for code review, fix what review surfaces. |
| Sat | Write `notes/weekN.md`. Rehearse the interview gate out loud. |
| Sun | Off. Consolidation is not optional at this pace. |

Take the Sunday. Six weeks at 20+ hours is a real load, and the failure
mode here is not running out of ability — it is running out of steam in
week 5, which is exactly when the interesting part starts.
