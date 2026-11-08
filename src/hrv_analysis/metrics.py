"""Time-domain HRV metrics.

Definitions follow Table 1 of the Task Force of the European Society of
Cardiology and the North American Society of Pacing and Electrophysiology
(1996), "Heart rate variability: standards of measurement, physiological
interpretation and clinical use", Eur Heart J 17:354-381 / Circulation
93:1043-1065:

- SDNN  -- standard deviation of all NN intervals.
- RMSSD -- square root of the mean of the sum of the squares of
  differences between adjacent NN intervals.
- SDSD  -- standard deviation of differences between adjacent NN intervals.
- NN50  -- number of pairs of adjacent NN intervals differing by more
  than 50 ms; pNN50 = NN50 / total number of NN intervals.

Conventions used here (documented, since the Task Force text leaves
them implicit):

- SDNN and SDSD use the *population* standard deviation (denominator N
  and N-1 for the N-1 successive differences respectively, i.e.
  ``numpy.std`` with ``ddof=0``). This matches the usual HRV-toolbox
  convention for SDNN.
- pNN50 divides NN50 by the number of successive differences (N-1),
  the denominator used by most implementations; the Task Force table
  text ("divided by the total number of all NN intervals") is ambiguous
  between N and N-1 and differs by at most one beat for any real
  recording.
- "RR intervals" here are the input series as given. Strictly, the
  Task Force metrics are defined on *NN* intervals (normal-to-normal,
  artifacts removed). The input is assumed to be already cleaned NN
  intervals; see :func:`validate_rr` for the sanity checks applied.

Units: input RR intervals in milliseconds; all metrics in ms except
mean HR (bpm), pNN50 (%) and CV (%).
"""

from __future__ import annotations

import math

import numpy as np

#: Minimum plausible RR interval (ms). Values outside [300, 2000] ms
#: (200 bpm / 30 bpm) are almost certainly artifacts or unit errors.
MIN_RR_MS = 300.0
MAX_RR_MS = 2000.0

#: Minimum number of intervals needed for a meaningful result.
MIN_INTERVALS = 2


def validate_rr(rr: np.ndarray) -> np.ndarray:
    """Validate an RR series and return it as a float array (ms).

    Raises
    ------
    ValueError
        If the series is empty, has fewer than two intervals, contains
        non-finite values, or contains values outside 300-2000 ms.
    """
    rr = np.asarray(rr, dtype=float).ravel()
    if rr.size < MIN_INTERVALS:
        raise ValueError(
            f"need at least {MIN_INTERVALS} RR intervals, got {rr.size}"
        )
    if not np.all(np.isfinite(rr)):
        raise ValueError("RR intervals must be finite numbers")
    if np.any(rr <= 0):
        raise ValueError("RR intervals must be positive")
    bad = rr[(rr < MIN_RR_MS) | (rr > MAX_RR_MS)]
    if bad.size:
        raise ValueError(
            f"{bad.size} RR interval(s) outside plausible range "
            f"{MIN_RR_MS:.0f}-{MAX_RR_MS:.0f} ms "
            f"(min {rr.min():.1f}, max {rr.max():.1f}); "
            "check units (expected ms) or remove artifacts"
        )
    return rr


def successive_differences(rr: np.ndarray) -> np.ndarray:
    """Differences between adjacent RR intervals (ms)."""
    return np.diff(np.asarray(rr, dtype=float))


def compute_time_domain(rr) -> dict:
    """Compute time-domain HRV metrics from RR intervals (ms).

    Parameters
    ----------
    rr : array-like of float
        RR (NN) intervals in milliseconds.

    Returns
    -------
    dict with keys: ``n_intervals``, ``mean_rr_ms``, ``mean_hr_bpm``,
    ``sdnn_ms``, ``rmssd_ms``, ``sdsd_ms``, ``nn50``, ``pnn50_pct``,
    ``cv_pct``, ``min_rr_ms``, ``max_rr_ms``.
    """
    rr = validate_rr(rr)
    diffs = successive_differences(rr)

    mean_rr = float(np.mean(rr))
    sdnn = float(np.std(rr, ddof=0))
    rmssd = float(math.sqrt(np.mean(diffs ** 2)))
    sdsd = float(np.std(diffs, ddof=0))
    nn50 = int(np.sum(np.abs(diffs) > 50.0))
    pnn50 = 100.0 * nn50 / diffs.size

    return {
        "n_intervals": int(rr.size),
        "mean_rr_ms": mean_rr,
        "mean_hr_bpm": 60000.0 / mean_rr,
        "sdnn_ms": sdnn,
        "rmssd_ms": rmssd,
        "sdsd_ms": sdsd,
        "nn50": nn50,
        "pnn50_pct": pnn50,
        "cv_pct": 100.0 * sdnn / mean_rr,
        "min_rr_ms": float(np.min(rr)),
        "max_rr_ms": float(np.max(rr)),
    }


def format_time_domain(metrics: dict) -> str:
    """Render time-domain metrics as a plain-text table."""
    rows = [
        ("Intervals (N)", f"{metrics['n_intervals']}"),
        ("Mean RR", f"{metrics['mean_rr_ms']:.2f} ms"),
        ("Mean HR", f"{metrics['mean_hr_bpm']:.2f} bpm"),
        ("SDNN", f"{metrics['sdnn_ms']:.2f} ms"),
        ("RMSSD", f"{metrics['rmssd_ms']:.2f} ms"),
        ("SDSD", f"{metrics['sdsd_ms']:.2f} ms"),
        ("NN50", f"{metrics['nn50']}"),
        ("pNN50", f"{metrics['pnn50_pct']:.2f} %"),
        ("CV (SDNN/mean RR)", f"{metrics['cv_pct']:.2f} %"),
        ("RR range", f"{metrics['min_rr_ms']:.1f} - {metrics['max_rr_ms']:.1f} ms"),
    ]
    width = max(len(k) for k, _ in rows)
    lines = ["Time-domain HRV metrics", "-" * 34]
    lines += [f"{k:<{width}}  {v}" for k, v in rows]
    return "\n".join(lines)
