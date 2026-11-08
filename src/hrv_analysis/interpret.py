"""Plain-language interpretation of HRV results.

The bands below are a *rough orientation* for short-term (~5 min)
resting recordings, taken from the meta-analysis of Nunan et al.
(2010) as tabulated by Shaffer & Ginsberg (2017, Table 6):

- SDNN:  mean 50 ms, SD 16 ms, observed range 32-93 ms (27 studies)
- RMSSD: mean 42 ms, SD 15 ms, observed range 19-75 ms (15 studies)
- LF/HF: mean 2.8, SD 2.6, observed range 1.1-11.6 (25 studies)

Shaffer & Ginsberg stress that norms depend on recording length, age,
sex, posture, breathing and fitness, and that 24 h, short-term and
ultra-short-term values are NOT interchangeable. This module therefore
labels values only as "below / within / above the published
short-term range" and always prints the caveat. It is not a medical
diagnosis -- see README.
"""

from __future__ import annotations

# (low, high) = published short-term range (Nunan et al. 2010 via
# Shaffer & Ginsberg 2017, Table 6); mean shown for context.
REFERENCE_RANGES = {
    "sdnn_ms": (32.0, 93.0, 50.0),
    "rmssd_ms": (19.0, 75.0, 42.0),
    "lf_hf_ratio": (1.1, 11.6, 2.8),
}


def _band(value: float, low: float, high: float) -> str:
    if value < low:
        return "below the published short-term range"
    if value > high:
        return "above the published short-term range"
    return "within the published short-term range"


def interpret(time_metrics: dict, freq_metrics: dict | None = None) -> list[str]:
    """Return short interpretation lines for a metrics dict."""
    lines = []
    for key, label in (
        ("sdnn_ms", "SDNN"),
        ("rmssd_ms", "RMSSD"),
    ):
        low, high, mean = REFERENCE_RANGES[key]
        lines.append(
            f"{label} {time_metrics[key]:.1f} ms is "
            f"{_band(time_metrics[key], low, high)} "
            f"(short-term healthy mean ~{mean:.0f} ms)."
        )
    if freq_metrics is not None:
        low, high, mean = REFERENCE_RANGES["lf_hf_ratio"]
        lines.append(
            f"LF/HF {freq_metrics['lf_hf_ratio']:.2f} is "
            f"{_band(freq_metrics['lf_hf_ratio'], low, high)} "
            f"(short-term healthy mean ~{mean:.1f}). "
            "LF/HF is not a clean index of sympathovagal balance; "
            "interpret with caution (Shaffer & Ginsberg 2017)."
        )
    lines.append(
        "Orientation only, for a ~5 min resting recording: norms depend "
        "on age, posture, breathing and fitness, and this tool is not "
        "a medical device."
    )
    return lines
