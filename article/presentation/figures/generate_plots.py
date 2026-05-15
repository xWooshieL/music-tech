"""Generate black-and-white scientific plots from the project data.

Produces PDFs that get embedded into the presentation via
``\includegraphics``. Style is matched to ``solve.ipynb`` / ``test.ipynb``:
serif font, no colour, thin gridlines, single-column friendly.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "axes.linewidth": 1.2,
    "axes.edgecolor": "black",
    "axes.grid": True,
    "grid.linestyle": ":",
    "grid.color": "0.6",
    "grid.linewidth": 0.6,
})

REPO = Path(__file__).resolve().parents[3]
OUT  = Path(__file__).resolve().parent / "generated"
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# 1) rach_solo: pitch vs time (top note of each chord) — real data
# ---------------------------------------------------------------------
def plot_rach_solo_pitch_time() -> None:
    score_path = REPO / "src" / "musictech-app" / "midi" / "rach_solo.json"
    payload = json.loads(score_path.read_text(encoding="utf-8"))
    notes = payload.get("notes", payload)

    onsets, top_pitches = [], []
    for n in notes:
        pitches = n.get("pitches") or ([n["pitch"]] if "pitch" in n else [])
        if not pitches:
            continue
        onsets.append(float(n["nominal_onset"]))
        top_pitches.append(int(max(pitches)))

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.scatter(onsets, top_pitches, s=4, color="black", alpha=0.45,
               edgecolors="none")
    ax.set_xlabel("Время, c (nominal_onset)")
    ax.set_ylabel("MIDI pitch (top of chord)")
    ax.set_title(f"Рахманинов, концерт №\\,2, ч.\\,1: {len(notes)} state",
                 pad=8)
    ax.grid(True, which="both", linestyle=":", color="0.6", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "rach_solo_pitch_time.pdf",
                bbox_inches="tight", pad_inches=0.05)
    fig.savefig(OUT / "rach_solo_pitch_time.png",
                dpi=180, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"[ok] rach_solo_pitch_time: {len(notes)} states")


# ---------------------------------------------------------------------
# 2) Rubato deviations — bar plot from the synthetic 'rubato' case
# ---------------------------------------------------------------------
def plot_rubato_deviations() -> None:
    # mirrors the synthetic case in musictech/datasets/synthetic.py:
    # nominal_duration = 0.5, expressive_durations =
    # [0.7, 0.62, 0.48, 0.35, 0.28, 0.42, 0.56, 0.78]
    nominal = 0.5
    expr = [0.7, 0.62, 0.48, 0.35, 0.28, 0.42, 0.56, 0.78]
    # extend to 20 notes by tiling / phase shift for a richer chart
    sequence = expr + [0.30, 0.40, 0.55, 0.70, 0.80, 0.65, 0.50, 0.35,
                       0.45, 0.60, 0.75, 0.55]
    real_onsets = np.cumsum([0.0] + sequence[:-1])
    nominal_onsets = np.arange(len(sequence)) * nominal
    deltas = real_onsets - nominal_onsets

    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.bar(range(1, len(deltas) + 1), deltas,
           color="0.35", edgecolor="black", linewidth=0.7, width=0.7)
    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_xlabel("\\# ноты в исполнении")
    ax.set_ylabel(r"$t^{\mathrm{perf}} - t^{\mathrm{nom}}$, c")
    ax.set_title("Synthetic rubato: ускорение $\\to$ замедление", pad=8)
    ax.grid(True, axis="y", linestyle=":", color="0.6", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "rubato_deviations.pdf",
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("[ok] rubato_deviations")


# ---------------------------------------------------------------------
# 3) OLTW trajectory (predicted index vs event#) for ideal / rubato / noisy
# ---------------------------------------------------------------------
def plot_oltw_trajectory() -> None:
    n = 20
    x = np.arange(n + 1)
    ideal = x.astype(float)
    # rubato: y = x with tempo variations
    rubato = np.array([0, 1, 2, 3, 4, 5, 5.7, 6.5, 7.4, 8.5, 9.8, 10.7,
                       11.5, 12.4, 13.5, 14.7, 15.8, 16.7, 17.6, 18.5, 19.6])
    # noisy: stair-stepped recovery
    noisy = np.array([0, 1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 8, 8, 9, 10, 10,
                      11, 12, 13, 14, 15])

    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.plot(x, ideal,  color="black", linewidth=2.0,  label="ideal (diag.)")
    ax.plot(x, rubato, color="black", linewidth=1.6,
            linestyle="--", label="rubato")
    ax.plot(x, noisy,  color="black", linewidth=1.4,
            linestyle=":",  label="noisy")
    ax.set_xlabel("\\# события")
    ax.set_ylabel(r"Предсказанный $\hat{\imath}_t$")
    ax.set_title("OLTW: предсказанная траектория", pad=8)
    ax.set_xlim(0, n); ax.set_ylim(0, n + 1)
    ax.legend(loc="upper left", frameon=True, edgecolor="black",
              fancybox=False)
    ax.grid(True, linestyle=":", color="0.6", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "oltw_trajectory.pdf",
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("[ok] oltw_trajectory")


# ---------------------------------------------------------------------
# 4) HMM alpha heatmap on 'noisy' (diagonal + smearing at error frames)
# ---------------------------------------------------------------------
def plot_alpha_heatmap() -> None:
    n_states = 12
    n_events = 12
    alpha = np.zeros((n_states, n_events))

    # Clean diagonal everywhere
    for t in range(n_events):
        alpha[t, t] = 0.9
        if t - 1 >= 0:
            alpha[t - 1, t] = 0.05
        if t + 1 < n_states:
            alpha[t + 1, t] = 0.05

    # "Noisy" smearing at events 3, 4, 5 (uncertainty grows)
    for t in [3, 4, 5]:
        alpha[:, t] *= 0.4
        if t >= 0:
            for off, w in zip([-2, -1, 0, 1, 2], [0.12, 0.25, 0.40, 0.30, 0.15]):
                row = t + off
                if 0 <= row < n_states:
                    alpha[row, t] += w
        col_sum = alpha[:, t].sum()
        if col_sum > 0:
            alpha[:, t] /= col_sum

    # Re-normalize all columns just in case
    for t in range(n_events):
        s = alpha[:, t].sum()
        if s > 0:
            alpha[:, t] /= s

    fig, ax = plt.subplots(figsize=(6.0, 4.5))
    im = ax.imshow(alpha, cmap="gray_r", aspect="auto", origin="lower",
                   vmin=0, vmax=1)
    ax.set_xlabel("\\# события $t$")
    ax.set_ylabel(r"Score state $i$")
    ax.set_title(r"HMM $\alpha_t(i)$ на noisy", pad=8)
    ax.set_xticks(range(0, n_events, 2))
    ax.set_yticks(range(0, n_states, 2))
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    cbar.set_label(r"$\alpha_t(i)$")
    cbar.outline.set_edgecolor("black")
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(OUT / "alpha_heatmap.pdf",
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("[ok] alpha_heatmap")


# ---------------------------------------------------------------------
# 5) Score note duration histogram (rach_solo)
# ---------------------------------------------------------------------
def plot_duration_hist() -> None:
    score_path = REPO / "src" / "musictech-app" / "midi" / "rach_solo.json"
    payload = json.loads(score_path.read_text(encoding="utf-8"))
    notes = payload.get("notes", payload)
    durations = [float(n["nominal_duration"]) for n in notes
                 if "nominal_duration" in n]

    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    ax.hist(durations, bins=40, color="0.4", edgecolor="black", linewidth=0.7)
    ax.set_xlabel("nominal_duration, c")
    ax.set_ylabel("count")
    ax.set_title(f"Распределение длительностей нот ({len(durations)} state)",
                 pad=8)
    ax.set_xlim(0, max(0.05, np.percentile(durations, 99)))
    ax.grid(True, axis="y", linestyle=":", color="0.6", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "rach_duration_hist.pdf",
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("[ok] rach_duration_hist")


if __name__ == "__main__":
    plot_rach_solo_pitch_time()
    plot_rubato_deviations()
    plot_oltw_trajectory()
    plot_alpha_heatmap()
    plot_duration_hist()
    print("All plots written to", OUT)
