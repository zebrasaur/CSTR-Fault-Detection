#!/usr/bin/env python3
"""
Acceptance checks for the CSTR fault-detection build.

    python check.py          # status of every stage
    python check.py 3        # run stage 3 checks
    python check.py 3 --spec # print the interface stage 3 expects

These checks are the specification. They test BEHAVIOUR and INVARIANTS,
never implementation, so there are many correct ways to pass them and
none of them are visible from here.

A green stage means you built the right thing. It does not mean you built
it well -- ask for a code review at the end of each stage.

Only numpy and pandas are required.
"""

import argparse
import importlib
import os
import sys
import traceback

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
sys.path.insert(0, SRC)

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


# --------------------------------------------------------------------------
# Tiny test harness
# --------------------------------------------------------------------------

class Stage:
    def __init__(self, number, title, spec):
        self.number, self.title, self.spec = number, title, spec
        self.results = []

    def check(self, description, fn, hint=""):
        """Run one assertion. fn() should return True, or raise."""
        try:
            ok = fn()
            if ok is False:
                self.results.append((FAIL, description, hint))
            else:
                self.results.append((PASS, description, ""))
        except AssertionError as e:
            self.results.append((FAIL, description, str(e) or hint))
        except Exception as e:
            detail = f"{type(e).__name__}: {e}"
            self.results.append((FAIL, description, detail + ("  | " + hint if hint else "")))

    def report(self):
        width = 62
        print(f"\n{'=' * width}")
        print(f"Stage {self.number}: {self.title}")
        print("=" * width)
        for status, desc, hint in self.results:
            mark = "  ok  " if status == PASS else " FAIL "
            print(f"[{mark}] {desc}")
            if status == FAIL and hint:
                for line in hint.split("\n"):
                    print(f"          {line}")
        n_pass = sum(1 for r in self.results if r[0] == PASS)
        total = len(self.results)
        print("-" * width)
        if n_pass == total and total:
            print(f"Stage {self.number} COMPLETE  ({n_pass}/{total})")
        else:
            print(f"{n_pass}/{total} passing")
        return n_pass == total and total > 0


def load(module_name, stage):
    """Import a student module, or fail the stage with the interface spec."""
    try:
        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        return importlib.import_module(module_name)
    except ImportError:
        raise AssertionError(
            f"cannot import src/{module_name}.py -- does the file exist?\n"
            f"Run `python check.py {stage.number} --spec` for the interface.")


def needs(mod, *names):
    missing = [n for n in names if not hasattr(mod, n)]
    if missing:
        raise AssertionError(f"missing: {', '.join(missing)}")
    return True


# --------------------------------------------------------------------------
# Stage 1 -- Python mechanics
# --------------------------------------------------------------------------

SPEC1 = """src/warmup.py

    def moving_average(values, window):
        '''List of averages over each consecutive `window` values.
        Length is len(values) - window + 1.'''

    def standardize(values):
        '''(x - mean) / sample standard deviation, as a list.
        Sample sd divides by n-1.'''

    def count_consecutive_above(values, threshold, n):
        '''True if at least `n` consecutive values exceed `threshold`.'''

Write these in pure Python -- no numpy. You will reuse the third one.
"""


def stage1():
    s = Stage(1, "Python mechanics", SPEC1)
    s.check("src/warmup.py imports", lambda: load("warmup", s) is not None)
    try:
        w = load("warmup", s)
    except AssertionError:
        return s
    s.check("all three functions exist",
            lambda: needs(w, "moving_average", "standardize",
                          "count_consecutive_above"))

    def ma():
        assert w.moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5], \
            "moving_average([1,2,3,4], 2) should be [1.5, 2.5, 3.5]"
        assert len(w.moving_average(list(range(10)), 3)) == 8, \
            "length should be len(values) - window + 1"
        assert w.moving_average([5, 5, 5], 3) == [5.0], "constant input"
        return True
    s.check("moving_average correct", ma)

    def std():
        out = w.standardize([1, 2, 3, 4, 5])
        assert abs(sum(out)) < 1e-9, "standardized values must sum to ~0"
        var = sum(x * x for x in out) / (len(out) - 1)
        assert abs(var - 1.0) < 1e-9, \
            "sample variance of the result must be 1.0 -- are you dividing by n instead of n-1?"
        return True
    s.check("standardize correct (sample sd, n-1)", std)

    def consec():
        f = w.count_consecutive_above
        assert f([0, 5, 5, 5, 0], 1, 3) is True, "three 5s in a row exceed 1"
        assert f([0, 5, 5, 0, 5], 1, 3) is False, "not three in a ROW"
        assert f([5, 5, 5], 1, 3) is True, "run at the very start"
        assert f([0, 5, 5, 5], 1, 3) is True, "run at the very end"
        assert f([1, 1, 1], 1, 2) is False, "strictly greater than, not >="
        assert f([], 1, 1) is False, "empty input"
        return True
    s.check("count_consecutive_above correct (incl. edge cases)", consec)

    def pure():
        src = open(os.path.join(SRC, "warmup.py")).read()
        assert "import numpy" not in src and "from numpy" not in src, \
            "week 1 is pure Python -- no numpy yet"
        return True
    s.check("written in pure Python", pure)
    return s


# --------------------------------------------------------------------------
# Stage 2 -- numpy and the integrator
# --------------------------------------------------------------------------

SPEC2 = """src/integrate.py

    def rk4_step(f, y, t, dt):
        '''One classical 4th-order Runge-Kutta step.
        f(y, t) returns dy/dt as a numpy array. Returns the new y.'''

Verify it yourself three ways before running this check:
  1. against an analytic solution
  2. convergence order (halve dt, error should drop ~16x)
  3. a conserved quantity (harmonic oscillator energy)
"""


def stage2():
    s = Stage(2, "numpy and the integrator", SPEC2)
    try:
        m = load("integrate", s)
    except AssertionError as e:
        s.check("src/integrate.py imports", lambda: (_ for _ in ()).throw(e))
        return s
    s.check("src/integrate.py imports", lambda: True)
    s.check("rk4_step exists", lambda: needs(m, "rk4_step"))

    def decay():
        f = lambda y, t: -0.5 * y
        y = np.array([1.0])
        dt = 0.01
        for i in range(200):
            y = m.rk4_step(f, y, i * dt, dt)
        exact = np.exp(-0.5 * 2.0)
        err = abs(float(y[0]) - exact)
        assert err < 1e-8, (
            f"after integrating dy/dt=-0.5y to t=2, got {float(y[0]):.8f}, "
            f"expected {exact:.8f} (error {err:.2e}).\n"
            "RK4 should be far more accurate than this.")
        return True
    s.check("matches analytic solution of dy/dt = -ky", decay)

    def order():
        f = lambda y, t: -0.5 * y
        exact = np.exp(-0.5 * 1.0)

        def err_at(dt):
            y = np.array([1.0])
            for i in range(int(round(1.0 / dt))):
                y = m.rk4_step(f, y, i * dt, dt)
            return abs(float(y[0]) - exact)

        e1, e2 = err_at(0.1), err_at(0.05)
        ratio = e1 / max(e2, 1e-18)
        assert 8 < ratio < 40, (
            f"halving dt changed the error by {ratio:.1f}x; 4th-order "
            "should be ~16x.\n"
            "A ratio near 2 means you have written Euler's method.\n"
            "A ratio near 4 means second-order -- check your k2/k3 weights.")
        return True
    s.check("convergence is 4th order (~16x)", order)

    def energy():
        # harmonic oscillator: y = [position, velocity]
        f = lambda y, t: np.array([y[1], -y[0]])
        y = np.array([1.0, 0.0])
        e0 = 0.5 * (y[0] ** 2 + y[1] ** 2)
        dt = 0.01
        for i in range(2000):
            y = m.rk4_step(f, y, i * dt, dt)
        e1 = 0.5 * (y[0] ** 2 + y[1] ** 2)
        drift = abs(e1 - e0) / e0
        assert drift < 1e-6, (
            f"oscillator energy drifted by {drift:.2e} over 20 periods")
        return True
    s.check("conserves energy on a harmonic oscillator", energy)

    def vector():
        f = lambda y, t: np.array([-y[0], -2 * y[1], -3 * y[2]])
        y = m.rk4_step(f, np.array([1.0, 1.0, 1.0]), 0.0, 0.01)
        assert np.asarray(y).shape == (3,), \
            f"expected shape (3,), got {np.asarray(y).shape} -- rk4_step must handle vector states"
        return True
    s.check("handles vector-valued states", vector)

    def notime():
        # f that genuinely depends on t; catches ignoring the t argument
        f = lambda y, t: np.array([t])
        y = np.array([0.0])
        for i in range(100):
            y = m.rk4_step(f, y, i * 0.01, 0.01)
        assert abs(float(y[0]) - 0.5) < 1e-9, (
            f"integrating dy/dt = t from 0 to 1 should give 0.5, got {float(y[0]):.6f}.\n"
            "Are you passing t through to f correctly in the k2/k3/k4 stages?")
        return True
    s.check("uses the time argument correctly", notime)
    return s


# --------------------------------------------------------------------------
# Stage 3 -- the reactor
# --------------------------------------------------------------------------

SPEC3 = """src/cstr.py

    def default_params():
        '''Return your parameter bundle (a dataclass is a good choice).'''

    def solve_steady_state(T_target, params=None):
        '''Return (Ca, T, Tc, qc, conversion) from the design algebra.'''

    def stability_margin(T_target, params=None):
        '''Return (dQgen_dT, dQremoved_dT), per unit reactor volume.'''

    def simulate(duration=..., seed=..., **kwargs):
        '''Run the reactor closed-loop. Return a dict of numpy arrays
        including at least: time, T, Tc, Ca, qc'''

simulate() must accept `duration` and `seed` as keyword arguments.
Faults are checked by hand -- see the checklist this stage prints.
"""


def stage3():
    s = Stage(3, "the reactor", SPEC3)
    try:
        c = load("cstr", s)
    except AssertionError as e:
        s.check("src/cstr.py imports", lambda: (_ for _ in ()).throw(e))
        return s
    s.check("src/cstr.py imports", lambda: True)
    s.check("required functions exist",
            lambda: needs(c, "default_params", "solve_steady_state",
                          "stability_margin", "simulate"))

    T_target = 400.0

    def ss_shape():
        out = c.solve_steady_state(T_target)
        assert len(out) == 5, "expected (Ca, T, Tc, qc, conversion)"
        Ca, T, Tc, qc, conv = out
        assert abs(T - T_target) < 1e-6, "returned T should be the target"
        assert 0 < conv < 1, f"conversion {conv} must be a fraction"
        assert Tc < T, "jacket must be colder than the reactor to remove heat"
        assert qc > 0, "coolant flow must be positive"
        assert Ca > 0, "concentration must be positive"
        return True
    s.check("solve_steady_state is physically sensible", ss_shape)

    def stable():
        gen, rem = c.stability_margin(T_target)
        assert gen > 0 and rem > 0, "both sensitivities should be positive"
        assert rem > gen, (
            f"dQremoved/dT ({rem:.1f}) must exceed dQgen/dT ({gen:.1f}) "
            "or your operating point is open-loop unstable.\n"
            "This CSTR has three steady states -- you may be on the "
            "middle branch. Try the high-conversion branch.")
        return True
    s.check("operating point is open-loop stable (van Heerden)", stable)

    def runs():
        out = c.simulate(duration=200.0, seed=1)
        assert isinstance(out, dict), "simulate should return a dict of arrays"
        for k in ["time", "T", "Tc", "Ca", "qc"]:
            assert k in out, f"missing logged tag '{k}'"
        n = len(out["time"])
        assert n > 50, "not enough logged samples"
        for k, v in out.items():
            v = np.asarray(v, dtype=float)
            assert len(v) == n, f"tag '{k}' has length {len(v)}, expected {n}"
            assert np.isfinite(v).all(), (
                f"tag '{k}' contains NaN or inf -- the simulation diverged.\n"
                "Check your operating point and controller gain.")
        return True
    s.check("simulate() runs and returns finite aligned arrays", runs)

    def holds():
        out = c.simulate(duration=300.0, seed=2)
        T = np.asarray(out["T"], dtype=float)
        tail = T[len(T) // 2:]
        off = abs(tail.mean() - T_target)
        assert off < 1.0, (
            f"mean reactor temperature in the second half is {tail.mean():.2f} K, "
            f"{off:.2f} K off the 400 K setpoint.\n"
            "The controller should hold setpoint with no steady-state offset "
            "-- is the integral term working?")
        assert tail.std() < 5.0, (
            f"temperature standard deviation {tail.std():.2f} K is large -- "
            "the loop may be oscillating. Try reducing the controller gain.")
        return True
    s.check("closed loop holds setpoint with no offset", holds)

    def consistent():
        Ca, T, Tc, qc, conv = c.solve_steady_state(T_target)
        out = c.simulate(duration=300.0, seed=3)
        sim_Ca = np.asarray(out["Ca"], dtype=float)[-100:].mean()
        rel = abs(sim_Ca - Ca) / Ca
        assert rel < 0.15, (
            f"simulated Ca ({sim_Ca:.5f}) disagrees with your steady-state "
            f"algebra ({Ca:.5f}) by {rel * 100:.1f}%.\n"
            "One of the two is wrong. This is the most valuable bug in the "
            "project -- the algebra and the ODEs must agree.")
        return True
    s.check("simulation agrees with the steady-state algebra", consistent)

    def deterministic():
        a = c.simulate(duration=100.0, seed=7)
        b = c.simulate(duration=100.0, seed=7)
        assert np.allclose(np.asarray(a["T"], dtype=float),
                           np.asarray(b["T"], dtype=float)), \
            "same seed must give identical output, or nothing is reproducible"
        d = c.simulate(duration=100.0, seed=8)
        assert not np.allclose(np.asarray(a["T"], dtype=float),
                               np.asarray(d["T"], dtype=float)), \
            "different seeds must give different noise"
        return True
    s.check("seeding is reproducible and actually varies", deterministic)

    print("\n  Manual checklist for this stage (check.py cannot verify these):")
    for line in [
        "[ ] fouling implemented: UA decays, coolant flow rises to compensate",
        "[ ] reactor temperature stays near setpoint DURING the fouling fault",
        "[ ] a second fault implemented (coolant supply loss is easiest)",
        "[ ] measurement noise on every logged tag",
        "[ ] slow drifting feed disturbances, so 'normal' is not constant",
        "[ ] anti-windup on the PI integral term",
        "[ ] notes/week3.md contains your steady-state algebra",
    ]:
        print("   ", line)
    return s


# --------------------------------------------------------------------------
# Stage 4 -- dataset
# --------------------------------------------------------------------------

SPEC4 = """src/generate_data.py, writing into data/

Produce data/train.csv, data/val.csv, data/test.csv with at least:
    run_id, time, fault_kind, and your measured tags

Rules the checker enforces:
  * the three splits share no run_id
  * train and val contain ONLY normal runs (fault_kind == 'none')
  * test contains normal runs AND faulted runs
  * faulted runs span a range of severities, not one value
"""


def stage4():
    s = Stage(4, "dataset and splits", SPEC4)
    import pandas as pd
    data = os.path.join(HERE, "data")

    def exists():
        missing = [f for f in ["train.csv", "val.csv", "test.csv"]
                   if not os.path.exists(os.path.join(data, f))]
        assert not missing, f"data/ is missing: {', '.join(missing)}"
        return True
    s.check("data/train.csv, val.csv, test.csv exist", exists)
    if s.results[-1][0] == FAIL:
        return s

    frames = {n: pd.read_csv(os.path.join(data, f"{n}.csv"))
              for n in ["train", "val", "test"]}

    def cols():
        for n, df in frames.items():
            for col in ["run_id", "time", "fault_kind"]:
                assert col in df.columns, f"{n}.csv missing column '{col}'"
        return True
    s.check("required columns present", cols)

    def disjoint():
        ids = {n: set(df.run_id) for n, df in frames.items()}
        for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
            overlap = ids[a] & ids[b]
            assert not overlap, (
                f"{len(overlap)} run_id(s) appear in both {a} and {b}.\n"
                "Splits must be disjoint or every downstream number is invalid.")
        return True
    s.check("splits are disjoint", disjoint)

    def clean_train():
        for n in ["train", "val"]:
            kinds = set(frames[n].fault_kind.unique())
            assert kinds <= {"none"}, (
                f"{n}.csv contains faulted runs: {kinds - {'none'}}\n"
                "Detection is fitted on healthy data only. Faults belong "
                "in test.")
        return True
    s.check("train and val contain only normal runs", clean_train)

    def test_mixed():
        kinds = set(frames["test"].fault_kind.unique())
        assert "none" in kinds, (
            "test.csv has no normal runs -- you cannot measure a false "
            "alarm rate without them")
        assert len(kinds) >= 3, (
            f"test.csv has only {len(kinds)} fault kind(s): {kinds}. "
            "Aim for at least two fault types plus normal.")
        return True
    s.check("test contains normal and faulted runs", test_mixed)

    def enough():
        for n, df in frames.items():
            k = df.run_id.nunique()
            floor = 15 if n == "train" else 20
            assert k >= floor, (
                f"{n} has only {k} runs; aim for at least {floor}.\n"
                "Small splits give confidence intervals too wide to conclude "
                "anything.")
        return True
    s.check("splits are large enough to conclude anything", enough)

    def severities():
        t = frames["test"]
        if "severity" not in t.columns:
            raise AssertionError(
                "test.csv has no 'severity' column -- record it so you can "
                "show detection delay against fault magnitude")
        for kind, g in t[t.fault_kind != "none"].groupby("fault_kind"):
            u = g.groupby("run_id").severity.first().nunique()
            assert u > 3, (
                f"fault '{kind}' has only {u} distinct severity value(s).\n"
                "Randomise severity or your detection rate is tuned to one "
                "convenient magnitude.")
        return True
    s.check("fault severity is randomised", severities)

    print("\n  Manual checklist for this stage:")
    for line in [
        "[ ] the 'money plot' exists: healthy vs fouling, 4 panels",
        "[ ] reactor temperature is visually indistinguishable between them",
        "[ ] coolant flow visibly diverges",
        "[ ] ground-truth channels logged but kept out of the model inputs",
    ]:
        print("   ", line)
    return s


# --------------------------------------------------------------------------
# Stage 5 -- detection
# --------------------------------------------------------------------------

SPEC5 = """src/monitoring.py

    def fit_pca(X, n_components):
        '''X is (n_samples, n_tags) of NORMAL data. Standardize internally.
        Return a model (dict or object) exposing at least:
            mean, std, loadings (n_tags, n_components), eigenvalues'''

    def t2_q(X, model):
        '''Return (T2, Q), each of length n_samples.'''

    def alarms(stat, threshold, persistence):
        '''Boolean array, True from the first latched alarm onwards.
        An alarm latches after `persistence` consecutive exceedances.'''

Plus results/summary.csv with columns:
    method, category, n, rate, median_delay
and one row where category == 'normal' holding your false alarm rate.
"""


def _get(model, name):
    if isinstance(model, dict):
        assert name in model, f"model dict missing key '{name}'"
        return model[name]
    assert hasattr(model, name), f"model missing attribute '{name}'"
    return getattr(model, name)


def stage5():
    s = Stage(5, "detection", SPEC5)
    try:
        m = load("monitoring", s)
    except AssertionError as e:
        s.check("src/monitoring.py imports", lambda: (_ for _ in ()).throw(e))
        return s
    s.check("src/monitoring.py imports", lambda: True)
    s.check("required functions exist",
            lambda: needs(m, "fit_pca", "t2_q", "alarms"))

    rng = np.random.default_rng(0)
    # correlated synthetic data: 3 latent factors driving 6 tags
    Z = rng.standard_normal((400, 3))
    A = rng.standard_normal((3, 6))
    X = Z @ A + 0.05 * rng.standard_normal((400, 6))

    def orthonormal():
        model = m.fit_pca(X, 3)
        P = np.asarray(_get(model, "loadings"), dtype=float)
        assert P.shape == (6, 3), (
            f"loadings shape is {P.shape}, expected (6, 3) = (n_tags, n_components).\n"
            "If it is (3, 6) you need a transpose -- it is always the transpose.")
        G = P.T @ P
        assert np.allclose(G, np.eye(3), atol=1e-8), \
            "loadings columns must be orthonormal (P.T @ P should be the identity)"
        return True
    s.check("PCA loadings are orthonormal and correctly shaped", orthonormal)

    def reconstruction():
        model = m.fit_pca(X, 6)          # keep ALL components
        T2, Q = m.t2_q(X, model)
        Q = np.asarray(Q, dtype=float)
        assert Q.max() < 1e-6, (
            f"with all 6 components retained the residual Q should be ~0, "
            f"but max Q = {Q.max():.3e}.\n"
            "This is the single most useful PCA sanity check. If it fails, "
            "your projection or your reconstruction is wrong.")
        return True
    s.check("keeping all components gives ~zero residual", reconstruction)

    def nonneg():
        model = m.fit_pca(X, 3)
        T2, Q = m.t2_q(X, model)
        T2, Q = np.asarray(T2, float), np.asarray(Q, float)
        assert len(T2) == len(X) and len(Q) == len(X), \
            "T2 and Q must have one value per sample"
        assert (T2 >= -1e-9).all() and (Q >= -1e-9).all(), \
            "T2 and Q are sums of squares -- they cannot be negative"
        return True
    s.check("T2 and Q are non-negative, one per sample", nonneg)

    def detects():
        model = m.fit_pca(X, 3)
        # break the correlation structure: this should move Q, not T2 much
        Xf = X.copy()
        Xf[:, 0] += 6.0
        _, Qf = m.t2_q(Xf, model)
        _, Qn = m.t2_q(X, model)
        assert np.asarray(Qf).mean() > 10 * np.asarray(Qn).mean(), \
            "breaking the correlation between tags should raise Q sharply"
        return True
    s.check("Q responds to a broken correlation structure", detects)

    def alarm_logic():
        a = np.asarray(m.alarms(np.array([0, 0, 5, 5, 5, 0, 0]), 1.0, 3),
                       dtype=bool)
        assert a.shape == (7,), "alarms() must return one value per sample"
        assert not a[:2].any(), "no alarm before the exceedance"
        assert a[4], "alarm should have latched by the third exceedance"
        assert a[-1], "alarms latch -- once raised they stay raised"
        b = np.asarray(m.alarms(np.array([0, 5, 5, 0, 5, 5, 0]), 1.0, 3),
                       dtype=bool)
        assert not b.any(), "two-in-a-row must not trigger a 3-sample rule"
        return True
    s.check("alarm logic latches and requires persistence", alarm_logic)

    import pandas as pd
    res = os.path.join(HERE, "results", "summary.csv")

    def summary():
        assert os.path.exists(res), "results/summary.csv not found"
        df = pd.read_csv(res)
        for col in ["method", "category", "n", "rate", "median_delay"]:
            assert col in df.columns, f"summary.csv missing column '{col}'"
        assert df.method.nunique() >= 2, (
            "at least two methods required -- you need the univariate "
            "baseline to show the multivariate model is worth anything")
        cats = set(df.category.str.lower())
        assert any("normal" in c for c in cats), \
            "no 'normal' row -- where is your false alarm rate?"
        assert (df.rate.between(0, 1)).all(), \
            "rate should be a fraction between 0 and 1"
        return True
    s.check("results/summary.csv is present and well formed", summary)

    def far_sane():
        df = pd.read_csv(res)
        far = df[df.category.str.lower().str.contains("normal")].rate.max()
        assert far <= 0.35, (
            f"false alarm rate is {far * 100:.0f}%. Something is wrong -- "
            "either thresholds are far too tight, or they were fitted on "
            "the wrong data.")
        det = df[~df.category.str.lower().str.contains("normal")].rate.max()
        assert det > far, \
            "your best detection rate is no better than your false alarm rate"
        return True
    s.check("false alarm rate is plausible", far_sane)

    print("\n  Manual checklist for this stage:")
    for line in [
        "[ ] thresholds fitted on the VALIDATION split only",
        "[ ] univariate baseline is Bonferroni-corrected (fair comparison)",
        "[ ] detection delay measured from fault start, not run start",
        "[ ] alarms before the fault begins counted as false alarms",
        "[ ] confidence interval on every rate you report",
        "[ ] you can explain why accuracy is not in your results table",
    ]:
        print("   ", line)
    return s


# --------------------------------------------------------------------------
# Stage 6 -- dynamics and shipping
# --------------------------------------------------------------------------

SPEC6 = """Add to src/monitoring.py

    def lag_embed(X, n_lags):
        '''Stack each sample with the previous n_lags samples.
        X is ONE continuous run. Returns (n_samples - n_lags,
        n_tags * (n_lags + 1)).'''

Plus:
    results/sensitivity.csv   -- hyperparameter sweep
    README.md                 -- with a section on what did NOT work
    figures/                  -- at least three figures
"""


def stage6():
    s = Stage(6, "dynamics and shipping", SPEC6)
    import pandas as pd
    try:
        m = load("monitoring", s)
    except AssertionError as e:
        s.check("src/monitoring.py imports", lambda: (_ for _ in ()).throw(e))
        return s
    s.check("lag_embed exists", lambda: needs(m, "lag_embed"))

    def embed_shape():
        X = np.arange(20, dtype=float).reshape(10, 2)
        E = np.asarray(m.lag_embed(X, 2), dtype=float)
        assert E.shape == (8, 6), (
            f"lag_embed(10x2, n_lags=2) gave {E.shape}, expected (8, 6).\n"
            "You lose n_lags rows and multiply columns by (n_lags + 1).")
        return True
    s.check("lag_embed has the right shape", embed_shape)

    def embed_content():
        X = np.arange(20, dtype=float).reshape(10, 2)
        E = np.asarray(m.lag_embed(X, 2), dtype=float)
        first = E[0]
        assert set(first.tolist()) == {0., 1., 2., 3., 4., 5.}, (
            f"first embedded row is {first.tolist()}; it should contain "
            "rows 0, 1 and 2 of X in some consistent order")
        assert np.allclose(m.lag_embed(X, 0), X), \
            "lag_embed with n_lags=0 should return X unchanged"
        return True
    s.check("lag_embed stacks the right samples", embed_content)

    def sens():
        p = os.path.join(HERE, "results", "sensitivity.csv")
        assert os.path.exists(p), "results/sensitivity.csv not found"
        df = pd.read_csv(p)
        assert len(df) >= 6, \
            "sweep at least 6 configurations or the range means little"
        return True
    s.check("hyperparameter sweep recorded", sens)

    def improved():
        df = pd.read_csv(os.path.join(HERE, "results", "summary.csv"))
        assert df.method.nunique() >= 3, (
            "expected three methods by now: univariate, PCA, dynamic PCA")
        return True
    s.check("three methods compared", improved)

    def readme():
        p = os.path.join(HERE, "README.md")
        assert os.path.exists(p), "README.md not found"
        text = open(p).read().lower()
        assert len(text) > 1500, "README is very short for this much work"
        assert any(k in text for k in
                   ["did not work", "didn't work", "failed", "limitation"]), (
            "README has no section on what did not work or its limitations.\n"
            "This is the section that separates an engineer from someone "
            "who followed a tutorial. Do not skip it.")
        return True
    s.check("README covers limitations and failures", readme)

    def figs():
        d = os.path.join(HERE, "figures")
        n = len([f for f in os.listdir(d)
                 if f.endswith(".png")]) if os.path.isdir(d) else 0
        assert n >= 3, f"found {n} figures in figures/, expected at least 3"
        return True
    s.check("figures produced", figs)

    print("\n  Manual checklist before you publish:")
    for line in [
        "[ ] each run embedded SEPARATELY (never splice runs together)",
        "[ ] clone your own repo to a fresh folder and run it end to end",
        "[ ] README renders correctly on GitHub, images load",
        "[ ] you can give the 10-minute walkthrough with no notes",
        "[ ] notes/ has one file per week",
        "[ ] NOW ask to unlock the reference implementation and compare",
    ]:
        print("   ", line)
    return s


# --------------------------------------------------------------------------

STAGES = {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5, 6: stage6}
SPECS = {1: SPEC1, 2: SPEC2, 3: SPEC3, 4: SPEC4, 5: SPEC5, 6: SPEC6}
TITLES = {1: "Python mechanics", 2: "numpy and the integrator",
          3: "the reactor", 4: "dataset and splits",
          5: "detection", 6: "dynamics and shipping"}


def main():
    ap = argparse.ArgumentParser(description="Acceptance checks")
    ap.add_argument("stage", nargs="?", type=int, choices=sorted(STAGES))
    ap.add_argument("--spec", action="store_true",
                    help="print the interface this stage expects")
    args = ap.parse_args()

    if args.spec:
        if not args.stage:
            ap.error("--spec needs a stage number")
        print(SPECS[args.stage])
        return

    if args.stage:
        ok = STAGES[args.stage]().report()
        sys.exit(0 if ok else 1)

    print("\nProgress\n" + "-" * 40)
    for n in sorted(STAGES):
        try:
            st = STAGES[n]()
            done = all(r[0] == PASS for r in st.results) and st.results
            n_pass = sum(1 for r in st.results if r[0] == PASS)
            mark = "DONE" if done else f"{n_pass}/{len(st.results)}"
        except Exception:
            mark = "--"
        print(f"  Stage {n}  {TITLES[n]:28s} {mark}")
    print("\nRun `python check.py N` for detail on a stage.")


if __name__ == "__main__":
    main()
