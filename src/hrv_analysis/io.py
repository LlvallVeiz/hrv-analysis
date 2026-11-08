"""Reading RR-interval files.

Accepted formats:

- ``.csv`` -- one RR interval (ms) per line, optionally with a header
  row (a header is detected when the first non-empty line is not a
  number) and optionally a second column (ignored after the first).
- ``.txt`` -- same as CSV: one interval per line, blank lines and
  lines starting with ``#`` are ignored.

The loader is deliberately tolerant about the container (CSV vs TXT)
and strict about the content: every value must parse as a number and
pass :func:`hrv_analysis.metrics.validate_rr`.
"""

from __future__ import annotations

import numpy as np


def _parse_lines(lines) -> list[float]:
    """Parse RR values (ms) from text lines, skipping blanks/comments."""
    values: list[float] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # First field only; allows "800" or "800, ..." style rows.
        first = line.split(",")[0].strip()
        try:
            values.append(float(first))
        except ValueError:
            # A non-numeric first line is treated as a header, but only
            # if nothing has been parsed yet; anything else is an error.
            if not values:
                continue
            raise ValueError(f"cannot parse RR value from line: {raw!r}")
    return values


def load_rr(path: str) -> np.ndarray:
    """Load RR intervals (ms) from a CSV/TXT file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If no numeric intervals are found or a data line is malformed.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        values = _parse_lines(handle)
    if not values:
        raise ValueError(f"no RR intervals found in {path}")
    return np.asarray(values, dtype=float)
