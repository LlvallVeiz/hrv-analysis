"""Frequency-domain HRV metrics (Welch PSD of interpolated RR series).

Method (the standard textbook pipeline, Task Force 1996):

1. Build the time axis by cumulative sum of the RR intervals.
2. Interpolate the unevenly sampled RR tachogram onto an evenly
   spaced grid (cubic spline, 4 Hz) so a Fourier method applies.
3. Detrend (linear) and estimate the power spectral density with
   Welch's method (Hann window).
4. Integrate power in the Task Force bands:

   - VLF  0.0033 - 0.04 Hz
   - LF   0.04   - 0.15 Hz
   - HF   0.15   - 0.40 Hz

   Total power = VLF + LF + HF. Normal units (nu) divide a band's
   power by LF + HF (Task Force / Shaffer & Ginsberg 2017).

Caveats, stated honestly in the output:

- Frequency analysis needs a recording long enough to contain several
  cycles of the slowest band: a 5 min recording is the Task Force
  minimum for LF/HF; VLF is not interpretable from short recordings
  and is reported only for completeness.
- The LF/HF ratio is *not* a clean "sympathovagal balance" index;
  Shaffer & Ginsberg (2017) stress that the SNS/PNS relationship is
  not zero-sum and the ratio does not always index autonomic balance.
- Requires scipy. If scipy is missing, :func:`compute_frequency_domain`
  raises ImportError with a clear message.
"""

from __future__ import annotations

import numpy as np

#: Interpolation rate for the RR tachogram (Hz). 4 Hz is the common
#: choice (Task Force-era practice; e.g. 4 Hz in most toolboxes).
FS_HZ = 4.0

#: Task Force frequency bands (Hz).
BANDS = {
    "vlf": (0.0033, 0.04),
    "lf": (0.04, 0.15),
    "hf": (0.15, 0.40),
}

#: Minimum recording length (s) below which frequency results are
#: refused outright (fewer than ~2 LF cycles).
MIN_DURATION_S = 60.0


def _band_power(freqs: np.ndarray, psd: np.ndarray, lo: float, hi: float) -> float:
    """Integrate PSD over [lo, hi] Hz with the trapezoidal rule."""
    mask = (freqs >= lo) & (freqs <= hi)
    return float(np.trapezoid(psd[mask], freqs[mask]))


def compute_frequency_domain(rr) -> dict:
    """Compute frequency-domain HRV metrics from RR intervals (ms).

    Parameters
    ----------
    rr : array-like of float
        RR (NN) intervals in milliseconds.

    Returns
    -------
    dict with keys: ``duration_s``, ``vlf_ms2``, ``lf_ms2``,
    ``hf_ms2``, ``total_power_ms2``, ``lf_hf_ratio``, ``lf_nu``,
    ``hf_nu``, ``lf_peak_hz``, ``hf_peak_hz``.

    Raises
    ------
    ImportError
        If scipy is not installed.
    ValueError
        If the recording is shorter than 60 s.
    """
    try:
        from scipy.interpolate import CubicSpline
        from scipy.signal import welch
    except ImportError as exc:  # pragma: no cover - environment issue
        raise ImportError(
            "frequency-domain analysis needs scipy: pip install scipy"
        ) from exc

    from .metrics import validate_rr

    rr = validate_rr(rr)
    # Time axis in seconds: beat times are the cumulative RR sums.
    t_beat = np.cumsum(rr) / 1000.0
    duration = float(t_beat[-1])
    if duration < MIN_DURATION_S:
        raise ValueError(
            f"recording too short for frequency analysis: {duration:.1f} s "
            f"(minimum {MIN_DURATION_S:.0f} s)"
        )

    t_even = np.arange(0.0, t_beat[-1], 1.0 / FS_HZ)
    rr_interp = CubicSpline(t_beat, rr, extrapolate=True)(t_even)
    rr_interp = rr_interp - np.mean(rr_interp)
    # Linear detrend, matching common practice.
    rr_interp = rr_interp - np.linspace(
        rr_interp[0], rr_interp[-1], rr_interp.size
    ) + np.mean(rr_interp)

    nperseg = min(256, rr_interp.size)
    freqs, psd = welch(
        rr_interp, fs=FS_HZ, window="hann", nperseg=nperseg, scaling="density"
    )

    powers = {name: _band_power(freqs, psd, lo, hi) for name, (lo, hi) in BANDS.items()}
    total = sum(powers.values())
    lf_hf = powers["lf"] / powers["hf"] if powers["hf"] > 0 else float("inf")
    lf_plus_hf = powers["lf"] + powers["hf"]

    def _peak(lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs <= hi)
        return float(freqs[mask][int(np.argmax(psd[mask]))])

    return {
        "duration_s": duration,
        "vlf_ms2": powers["vlf"],
        "lf_ms2": powers["lf"],
        "hf_ms2": powers["hf"],
        "total_power_ms2": total,
        "lf_hf_ratio": float(lf_hf),
        "lf_nu": 100.0 * powers["lf"] / lf_plus_hf if lf_plus_hf > 0 else 0.0,
        "hf_nu": 100.0 * powers["hf"] / lf_plus_hf if lf_plus_hf > 0 else 0.0,
        "lf_peak_hz": _peak(*BANDS["lf"]),
        "hf_peak_hz": _peak(*BANDS["hf"]),
    }


def format_frequency_domain(metrics: dict) -> str:
    """Render frequency-domain metrics as a plain-text table."""
    rows = [
        ("Duration", f"{metrics['duration_s']:.1f} s"),
        ("VLF power (0.0033-0.04 Hz)", f"{metrics['vlf_ms2']:.1f} ms^2"),
        ("LF power (0.04-0.15 Hz)", f"{metrics['lf_ms2']:.1f} ms^2"),
        ("HF power (0.15-0.40 Hz)", f"{metrics['hf_ms2']:.1f} ms^2"),
        ("Total power", f"{metrics['total_power_ms2']:.1f} ms^2"),
        ("LF/HF ratio", f"{metrics['lf_hf_ratio']:.2f}"),
        ("LF (nu)", f"{metrics['lf_nu']:.1f}"),
        ("HF (nu)", f"{metrics['hf_nu']:.1f}"),
        ("LF peak", f"{metrics['lf_peak_hz']:.3f} Hz"),
        ("HF peak", f"{metrics['hf_peak_hz']:.3f} Hz"),
    ]
    width = max(len(k) for k, _ in rows)
    lines = ["Frequency-domain HRV metrics (Welch PSD, 4 Hz cubic interp.)",
             "-" * 58]
    lines += [f"{k:<{width}}  {v}" for k, v in rows]
    return "\n".join(lines)
