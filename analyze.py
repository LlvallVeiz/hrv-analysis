#!/usr/bin/env python3
"""Thin wrapper so the tool also runs as ``python analyze.py file.csv``."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hrv_analysis.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
