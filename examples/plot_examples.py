"""Generate the example plots: tachogram and Welch PSD.

Run from the project root:  python examples/plot_examples.py
Requires matplotlib and scipy (see requirements.txt).
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hrv_analysis.frequency import FS_HZ
from hrv_analysis.io import load_rr


def main() -> None:
    rr = load_rr("examples/sample_rr.csv")
    t_min = np.cumsum(rr) / 60000.0

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t_min, rr, lw=0.8)
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("RR interval (ms)")
    ax.set_title("RR tachogram — synthetic 5-min resting example (n=376)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("examples/tachogram.png", dpi=150)
    plt.close(fig)

    from scipy.interpolate import CubicSpline
    from scipy.signal import welch

    t_beat = np.cumsum(rr) / 1000.0
    t_even = np.arange(0.0, t_beat[-1], 1.0 / FS_HZ)
    series = CubicSpline(t_beat, rr)(t_even)
    series = series - series.mean()
    freqs, psd = welch(series, fs=FS_HZ, window="hann", nperseg=256)

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(freqs, psd, lw=0.9)
    ax.axvspan(0.04, 0.15, color="tab:orange", alpha=0.2, label="LF 0.04-0.15 Hz")
    ax.axvspan(0.15, 0.40, color="tab:green", alpha=0.2, label="HF 0.15-0.40 Hz")
    ax.set_xlim(0, 0.5)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("PSD (ms²/Hz)")
    ax.set_title("Welch PSD — peaks at 0.10 Hz (Mayer) and 0.25 Hz (RSA)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("examples/psd.png", dpi=150)
    plt.close(fig)
    print("wrote examples/tachogram.png and examples/psd.png")


if __name__ == "__main__":
    main()
