"""Command-line interface for hrv_analysis.

Usage:
    python -m hrv_analysis examples/sample_rr.csv
    python -m hrv_analysis examples/nsr16265_rr.csv --no-frequency
    python -m hrv_analysis data.csv --output report.txt
"""

from __future__ import annotations

import argparse
import sys

from .frequency import MIN_DURATION_S, compute_frequency_domain, format_frequency_domain
from .interpret import interpret
from .io import load_rr
from .metrics import compute_time_domain, format_time_domain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hrv_analysis",
        description="Compute HRV metrics (Task Force 1996 definitions) "
        "from a file of RR intervals in milliseconds.",
    )
    parser.add_argument("file", help="CSV/TXT file, one RR interval (ms) per line")
    parser.add_argument(
        "--no-frequency",
        action="store_true",
        help="skip frequency-domain metrics (Welch PSD)",
    )
    parser.add_argument(
        "--output", "-o", default=None, help="write the report to this file too"
    )
    return parser


def analyse(path: str, with_frequency: bool = True) -> str:
    """Run the full analysis on ``path`` and return the report text."""
    rr = load_rr(path)
    time_metrics = compute_time_domain(rr)

    sections = [f"HRV analysis: {path}", f"N = {time_metrics['n_intervals']} intervals",
                "", format_time_domain(time_metrics)]

    freq_metrics = None
    if with_frequency:
        try:
            freq_metrics = compute_frequency_domain(rr)
            sections += ["", format_frequency_domain(freq_metrics)]
        except ValueError as exc:
            sections += ["", f"Frequency-domain metrics skipped: {exc}"]

    duration_min = time_metrics["n_intervals"] * time_metrics["mean_rr_ms"] / 60000.0
    if with_frequency and freq_metrics is not None and duration_min < 5.0:
        sections += [
            "",
            f"Note: recording is {duration_min:.1f} min; frequency results "
            f"are most reliable for >= 5 min recordings (Task Force 1996).",
        ]
    elif with_frequency and freq_metrics is None:
        sections += [
            "",
            f"Note: frequency analysis needs >= {MIN_DURATION_S:.0f} s of data.",
        ]

    sections += ["", "Interpretation (rough orientation, not a diagnosis):"]
    sections += [f"  - {line}" for line in interpret(time_metrics, freq_metrics)]
    return "\n".join(sections) + "\n"


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = analyse(args.file, with_frequency=not args.no_frequency)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(report, end="")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(report)
        print(f"Report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
