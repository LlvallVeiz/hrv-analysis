# Research notes — hrv-analysis

How the metrics, formulas and reference values in this project were
chosen. Every claim below is traceable to a checked source; nothing
here is written from memory alone.

## 1. The standard: Task Force (1996)

The definitions of all time-domain metrics follow Table 1 of:

> Task Force of the European Society of Cardiology and the North
> American Society of Pacing and Electrophysiology (1996). "Heart rate
> variability: standards of measurement, physiological interpretation
> and clinical use." *European Heart Journal* 17:354–381; published
> simultaneously in *Circulation* 93:1043–1065.

Verified against the full text (EUR Heart J version) on 2026-11-08.
Table 1 states verbatim:

| Variable | Units | Description (Task Force Table 1) |
| --- | --- | --- |
| SDNN | ms | Standard deviation of all NN intervals. |
| SDANN | ms | Standard deviation of the averages of NN intervals in all 5-minute segments of the entire recording. |
| RMSSD | ms | The square root of the mean of the sum of the squares of differences between adjacent NN intervals. |
| SDNN index | ms | Mean of the standard deviations of all NN intervals for all 5-minute segments of the entire recording. |
| SDSD | ms | Standard deviation of differences between adjacent NN intervals. |
| NN50 | count | Number of pairs of adjacent NN intervals differing by more than 50 ms in the entire recording. |
| pNN50 | % | NN50 count divided by the total number of all NN intervals. |

The same paper recommends four measures for time-domain assessment:
SDNN (overall HRV), HRV triangular index (overall HRV), SDANN
(long-term components) and RMSSD (short-term components). This
project implements SDNN, RMSSD and SDSD plus NN50/pNN50; SDANN and
the triangular index need 24 h (or segmented) recordings and are out
of scope — see "Limitations" in the README.

Frequency bands are also from the Task Force: ULF ≤ 0.003 Hz,
VLF 0.0033–0.04 Hz, LF 0.04–0.15 Hz, HF 0.15–0.40 Hz. The Task Force
minimum recording for short-term frequency analysis is 5 minutes.

Two conventions the Task Force text leaves implicit are documented
explicitly in `src/hrv_analysis/metrics.py`:

- SDNN/SDSD use the **population** standard deviation (denominator N),
  the usual HRV-toolbox convention.
- pNN50 divides NN50 by the **number of successive differences**
  (N−1), the denominator used by most implementations; the Task Force
  table text ("total number of all NN intervals") is ambiguous
  between N and N−1 and differs by at most one beat.

## 2. Interpretation and norms: Shaffer & Ginsberg (2017)

> Shaffer, F. & Ginsberg, J. P. (2017). "An overview of heart rate
> variability metrics and norms." *Frontiers in Public Health* 5:258.
> doi:10.3389/fpubh.2017.00258 — PMC5624990, PMID 29034226.

Verified against the PMC full text on 2026-11-08. Points used:

- Frequency-band table (their Table 2) repeats the Task Force bands
  above; normal units (nu) = band power / (LF + HF).
- Short-term (~5 min) norms are **not interchangeable** with 24 h or
  ultra-short-term norms; they depend on recording length, age, sex,
  posture, breathing and fitness.
- The reference ranges used by `interpret.py` are the Nunan et al.
  (2010) meta-analysis values reproduced in their Table 6 (21,438
  healthy adults):

  | Measure | Mean (SD) | Range |
  | --- | --- | --- |
  | SDNN (ms) | 50 (16) | 32–93 |
  | RMSSD (ms) | 42 (15) | 19–75 |
  | LF (ms²) | 519 (291) | 193–1,009 |
  | HF (ms²) | 657 (777) | 83–3,630 |
  | LF/HF | 2.8 (2.6) | 1.1–11.6 |

- The LF/HF ratio "may estimate" SNS/PNS balance only under
  controlled conditions; the SNS/PNS relationship is not zero-sum,
  so the ratio does not always index autonomic balance. The CLI
  prints this caveat with every interpretation.

## 3. Frequency-domain method

Pipeline: cumulative RR → time axis; cubic-spline interpolation to a
4 Hz even grid; linear detrend; Welch PSD (Hann window, `nperseg`
256); trapezoidal integration per band. This is the standard
textbook pipeline used by most HRV toolboxes; the 4 Hz rate and
Welch's method are the common defaults, not a Task Force prescription
(the Task Force specifies bands and minimum lengths, not the
estimator). The method is validated in-repo by two tests: a pure
0.10 Hz RR oscillation lands its power in LF (LF/HF > 10, peak
≈ 0.10 Hz) and a pure 0.25 Hz oscillation lands in HF (LF/HF < 0.1,
peak ≈ 0.25 Hz).

## 4. Example data

### Real data — MIT-BIH Normal Sinus Rhythm Database

`examples/nsr16265_rr.csv` holds the first 5 minutes of record
16265 (32-year-old male, healthy): 480 NN intervals, mean RR
622.5 ms, range 531.2–796.9 ms. Beat annotations were read from the
PhysioNet `nsrdb` (v1.0.0) `.atr` file at 128 Hz; only intervals
between two consecutive `N` (normal) beats were kept (483 RR → 480
NN; the record's first and last annotations are non-`N` markers).
Downloaded 2026-11-08 from
`https://physionet.org/files/nsrdb/1.0.0/16265.atr` (redirects to the
PhysioNet S3 mirror). Original database:

> Goldberger, A. L. et al. (2000). "PhysioBank, PhysioToolkit, and
> PhysioNet: components of a new research resource for complex
> physiologic signals." *Circulation* 101(23):e215–e220.
> Database: https://physionet.org/content/nsrdb/1.0.0/

Note the direct `wfdb` download from this sandbox failed (proxy
block); the `.atr` file was fetched with `curl -L` and parsed
locally with `wfdb` 4.3.1 — same bytes, same parser, documented
honestly here. The example is a single healthy subject's resting
segment, not a normative sample.

### Synthetic data

`examples/sample_rr.csv` (376 intervals, ~5 min) is generated by
`examples/generate_sample.py`: mean RR 800 ms + RSA 0.25 Hz
(25 ms) + Mayer wave 0.1 Hz (15 ms) + Gaussian noise σ = 8 ms,
seed 42. Its PSD peaks (LF 0.094 Hz, HF 0.250 Hz) recover the two
frequencies that were put in — a built-in sanity check of the
frequency pipeline.

## References

1. Task Force of the European Society of Cardiology and the North
   American Society of Pacing and Electrophysiology (1996). Heart rate
   variability: standards of measurement, physiological interpretation
   and clinical use. *Eur Heart J* 17:354–381.
   (also *Circulation* 93:1043–1065).
2. Shaffer, F. & Ginsberg, J. P. (2017). An overview of heart rate
   variability metrics and norms. *Front Public Health* 5:258.
   doi:10.3389/fpubh.2017.00258 —
   https://pmc.ncbi.nlm.nih.gov/articles/PMC5624990/
3. Nunan, D. et al. (2010). A quantitative systematic review of
   normal values for short-term heart rate variability in healthy
   adults. *Pacing Clin Electrophysiol* 33(11):1407–1417
   (values as reproduced in ref. 2, Table 6).
4. Goldberger, A. L. et al. (2000). PhysioBank, PhysioToolkit, and
   PhysioNet. *Circulation* 101(23):e215–e220.
   MIT-BIH Normal Sinus Rhythm Database:
   https://physionet.org/content/nsrdb/1.0.0/
