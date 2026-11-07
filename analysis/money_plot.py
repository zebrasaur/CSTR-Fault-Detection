"""Money plot: a healthy run and a fouled run, same seed, four measured signals.

A 30 % loss of UA, ramped in over days 3-6, is hidden in reactor temperature
(and so in outlet concentration) by the temperature controller, but shows
plainly in coolant flow and jacket temperature.

Run from the repo root:   python analysis/money_plot.py
Output:                   figures/money_plot.png
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from cstr import simulate
from faults import FaultType, FaultEvent


# ---- Block 1: the scenario ---------------------------------------------
SEED = 3                    # both runs share it, so drift and noise are identical
DAYS = 14
ONSET = 3 * 1440.0          # min; fouling starts on day 3
RAMP = 3 * 1440.0           # min; full severity on day 6
SEVERITY = 0.30             # fraction of UA lost
LOG_EVERY = 40              # 40 steps x 0.05 min = 2 min, as in the dataset

fouling = [FaultEvent(fault_type=FaultType.FOULING, t_start=ONSET,
                      severity=SEVERITY, ramp_duration=RAMP)]


# ---- Block 2: run both simulations and thin to 2-min rows ---------------
healthy = simulate(duration=DAYS * 1440.0, seed=SEED)
fouled = simulate(duration=DAYS * 1440.0, seed=SEED, faults=fouling)


def logged(run: dict) -> pd.DataFrame:
    """Keep every LOG_EVERY-th point of each array in a simulate() dict.

    Returns a DataFrame of shape (n_rows, n_keys), one column per key.
    """
    return pd.DataFrame({k: v[::LOG_EVERY] for k, v in run.items()})


h = logged(healthy)
f = logged(fouled)
h["day"] = h["time"] / 1440.0
f["day"] = f["time"] / 1440.0


# ---- Block 3: what goes in each panel, and the look ---------------------
PANELS = [                  # (column, title, unit)
    ("T",  "Reactor temperature",       "K"),
    ("qc", "Coolant flow",              "kg/min"),
    ("Tc", "Jacket temperature",        "K"),
    ("Ca", "Outlet concentration of A", "mol/m³"),
]
GRAY, ORANGE = "#8a8984", "#eb6834"
INK, MUTED, GRID, BAND = "#0b0b0b", "#52514e", "#e4e2dc", "#f2efe9"
SMOOTH = 60                 # rows; 60 x 2 min = 2-hour window


def smooth(s: pd.Series) -> pd.Series:
    """Centred 2-hour rolling mean; same length as s."""
    return s.rolling(SMOOTH, center=True, min_periods=1).mean()



# ---- Block 4: draw the four panels -------------------------------------
fig, axes = plt.subplots(4, 1, figsize=(9, 10.5), sharex=True)
fig.subplots_adjust(left=0.08, right=0.88, top=0.845, bottom=0.06, hspace=0.42)

for ax, (col, title, unit) in zip(axes, PANELS):
    ax.axvspan(ONSET / 1440, (ONSET + RAMP) / 1440, color=BAND, zorder=0)
    ax.plot(f["day"], f[col], color=ORANGE, lw=0.4, alpha=0.18)       # raw, fouled
    ax.plot(h["day"], h[col], color=GRAY,   lw=0.4, alpha=0.18)       # raw, healthy
    ax.plot(h["day"], smooth(h[col]), color=GRAY,   lw=3.2, label="Healthy")
    ax.plot(f["day"], smooth(f[col]), color=ORANGE, lw=1.6, label="Fouled (30 % UA loss)")
    ax.set_title(f"{title} ({unit})", loc="left", fontsize=10.5,
                 fontweight="bold", color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)

# direct labels at the right edge, where the two lines have separated
for ax, col in [(axes[1], "qc"), (axes[2], "Tc")]:
    ax.text(DAYS + 0.2, smooth(h[col]).iloc[-1], "healthy", color=MUTED,
            va="center", fontsize=9)
    ax.text(DAYS + 0.2, smooth(f[col]).iloc[-1], "fouled", color=ORANGE,
            va="center", fontsize=9, fontweight="bold")

axes[0].set_ylim(397, 403)
axes[0].legend(loc="lower right", frameon=False, ncol=2, fontsize=9)
axes[0].text((ONSET + RAMP / 2) / 1440, 402.3, "fouling ramps in",
             ha="center", color=MUTED, fontsize=9)
axes[-1].set_xlim(0, DAYS)
axes[-1].set_xlabel("Day", color=MUTED)

fig.text(0.01, 0.975, "The controller hides fouling in reactor temperature.",
         fontsize=15, fontweight="bold", color=INK)
fig.text(0.01, 0.948, "The coolant side gives it away.",
         fontsize=15, fontweight="bold", color=INK)
fig.text(0.01, 0.912,
         "Two simulations with the same seed: identical feed drift and sensor noise. "
         "Thin lines are measured\nsignals at 2-minute logging; "
         f"bold lines are 2-hour rolling means. Seed {SEED}.",
         fontsize=9, color=MUTED, va="top")

out = ROOT / "figures" / "money_plot.png"
fig.savefig(out, dpi=200)
print(f"saved {out}")


# ---- Block 5: the numbers behind the picture ---------------------------
last = slice(-720, None)    # last day: 720 rows of 2 min
for col, _, unit in PANELS:
    print(f"{col:3s} last-day mean   healthy {h[col][last].mean():8.2f}   "
          f"fouled {f[col][last].mean():8.2f}   {unit}")
d = np.abs(h["T_true"] - f["T_true"])
print(f"largest |T_true healthy - T_true fouled|: {d.max():.2f} K")
print(f"time at the valve limit after day 6: "
      f"{(f['qc_cmd'][f['day'] >= 6] >= 218.0).mean():.1%}")
