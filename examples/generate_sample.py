"""Generate ``sample_rr.csv``: a synthetic 5-minute resting RR series.

Model: mean RR 800 ms, respiratory sinus arrhythmia 0.25 Hz (25 ms
amplitude), Mayer wave 0.1 Hz (15 ms amplitude), Gaussian beat-to-beat
noise sigma 8 ms, NumPy seed 42. Output is clearly synthetic and is
only used to demonstrate the CLI and the plots.

Run:  python examples/generate_sample.py
"""

import numpy as np

SEED = 42
DURATION_S = 300.0


def generate(seed: int = SEED, duration_s: float = DURATION_S) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = 0.0
    rr: list[float] = []
    while t < duration_s:
        value = (
            800.0
            + 25.0 * np.sin(2 * np.pi * 0.25 * t)
            + 15.0 * np.sin(2 * np.pi * 0.10 * t)
            + rng.normal(0, 8.0)
        )
        rr.append(round(float(value), 1))
        t += value / 1000.0
    return np.array(rr)


if __name__ == "__main__":
    series = generate()
    with open("examples/sample_rr.csv", "w", encoding="utf-8") as handle:
        handle.write("rr_ms\n")
        for value in series:
            handle.write(f"{value:.1f}\n")
    print(
        f"wrote {len(series)} intervals, "
        f"duration {series.sum() / 1000:.1f} s, mean {series.mean():.1f} ms"
    )
