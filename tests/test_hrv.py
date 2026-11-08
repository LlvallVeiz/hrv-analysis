"""Tests for hrv_analysis, with hand-computed expected values.

Hand calculation for the reference series RR = [800, 850, 790, 820, 780] ms:

    successive differences:  50, -60, 30, -40
    squared differences:     2500, 3600, 900, 1600  -> sum 8600
    RMSSD = sqrt(8600 / 4) = sqrt(2150) = 46.368 ms

    mean RR = (800+850+790+820+780)/5 = 4040/5 = 808 ms
    deviations from mean: -8, 42, -18, 12, -28
    squared: 64, 1764, 324, 144, 784 -> sum 3080
    SDNN = sqrt(3080 / 5) = sqrt(616) = 24.819 ms  (population SD)

    mean of differences = (50-60+30-40)/4 = -5
    deviations of diffs from their mean: 55, -55, 35, -35
    squared: 3025, 3025, 1225, 1225 -> sum 8500
    SDSD = sqrt(8500 / 4) = sqrt(2125) = 46.098 ms

    |diff| > 50 ms: only |-60| -> NN50 = 1
    pNN50 = 1 / 4 differences = 25 %

    mean HR = 60000 / 808 = 74.257 bpm
    CV = SDNN / mean RR = 24.819 / 808 = 3.072 %
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pytest

from hrv_analysis.frequency import compute_frequency_domain
from hrv_analysis.io import load_rr
from hrv_analysis.metrics import compute_time_domain, validate_rr

RR_REF = [800, 850, 790, 820, 780]


def test_time_domain_hand_computed():
    m = compute_time_domain(RR_REF)
    assert m["n_intervals"] == 5
    assert m["mean_rr_ms"] == pytest.approx(808.0)
    assert m["mean_hr_bpm"] == pytest.approx(60000 / 808, rel=1e-9)
    assert m["sdnn_ms"] == pytest.approx(math.sqrt(616), rel=1e-9)
    assert m["rmssd_ms"] == pytest.approx(math.sqrt(2150), rel=1e-9)
    assert m["sdsd_ms"] == pytest.approx(math.sqrt(2125), rel=1e-9)
    assert m["nn50"] == 1
    assert m["pnn50_pct"] == pytest.approx(25.0)
    assert m["cv_pct"] == pytest.approx(100 * math.sqrt(616) / 808, rel=1e-9)
    assert m["min_rr_ms"] == 780.0
    assert m["max_rr_ms"] == 850.0


def test_constant_series_has_zero_variability():
    m = compute_time_domain([800] * 10)
    assert m["sdnn_ms"] == pytest.approx(0.0)
    assert m["rmssd_ms"] == pytest.approx(0.0)
    assert m["sdsd_ms"] == pytest.approx(0.0)
    assert m["pnn50_pct"] == pytest.approx(0.0)
    assert m["mean_hr_bpm"] == pytest.approx(75.0)


def test_pnn50_threshold_is_strictly_greater():
    # Differences exactly 50 ms must NOT count (Task Force: "more than 50 ms").
    m = compute_time_domain([800, 850, 800, 850, 800])
    assert m["nn50"] == 0
    assert m["pnn50_pct"] == pytest.approx(0.0)


def test_validate_rejects_bad_input():
    with pytest.raises(ValueError):
        validate_rr([])
    with pytest.raises(ValueError):
        validate_rr([800])
    with pytest.raises(ValueError):
        validate_rr([800, 0, 810])  # non-positive
    with pytest.raises(ValueError):
        validate_rr([800, 250, 810])  # implausible (< 300 ms)
    with pytest.raises(ValueError):
        validate_rr([800, 2500, 810])  # implausible (> 2000 ms)


def _oscillating_rr(freq_hz: float, amplitude_ms: float = 30.0, seconds: float = 300.0):
    """Deterministic RR series oscillating at one frequency.

    Beat times are built by integrating the instantaneous RR, so the
    series is a genuine (if idealised) tachogram, not a resampled sine.
    """
    t = 0.0
    rr = []
    while t < seconds:
        rr.append(800.0 + amplitude_ms * math.sin(2 * math.pi * freq_hz * t))
        t += rr[-1] / 1000.0
    return np.array(rr)


def test_frequency_lf_dominant_for_0_1_hz_oscillation():
    rr = _oscillating_rr(0.10)
    f = compute_frequency_domain(rr)
    assert f["lf_ms2"] > 10 * f["hf_ms2"]
    assert f["lf_hf_ratio"] > 10
    assert f["lf_peak_hz"] == pytest.approx(0.10, abs=0.02)


def test_frequency_hf_dominant_for_0_25_hz_oscillation():
    rr = _oscillating_rr(0.25)
    f = compute_frequency_domain(rr)
    assert f["hf_ms2"] > 10 * f["lf_ms2"]
    assert f["lf_hf_ratio"] < 0.1
    assert f["hf_peak_hz"] == pytest.approx(0.25, abs=0.02)


def test_frequency_refuses_short_recording():
    with pytest.raises(ValueError):
        compute_frequency_domain([800] * 30)  # ~24 s


def test_load_rr_csv_with_header_and_comments(tmp_path):
    path = tmp_path / "rr.csv"
    path.write_text("rr_ms\n800\n850\n# a comment\n790\n\n820\n")
    rr = load_rr(str(path))
    assert list(rr) == [800.0, 850.0, 790.0, 820.0]


def test_load_rr_rejects_garbage(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("800\nabc\n810\n")
    with pytest.raises(ValueError):
        load_rr(str(path))
