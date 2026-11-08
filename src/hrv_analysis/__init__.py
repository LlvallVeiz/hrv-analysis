"""hrv_analysis: heart rate variability (HRV) analysis from RR intervals.

Time-domain metrics follow the definitions of the Task Force of the
European Society of Cardiology and the North American Society of Pacing
and Electrophysiology (1996); frequency-domain bands follow the same
standard. See ``docs/RESEARCH.md`` for sources and formulas.
"""

from .metrics import compute_time_domain
from .frequency import compute_frequency_domain
from .io import load_rr

__all__ = ["compute_time_domain", "compute_frequency_domain", "load_rr"]
__version__ = "1.0.0"
