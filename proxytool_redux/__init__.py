"""REDUX_4 helpers: scoring utilities, bootstrap loader, and benchmark runner.

- Full exploratory notebook: ``proxytool_REDUX_4.ipynb``
- Slim reproducible runbook: ``proxytool_REDUX_4_REPRO.ipynb``
"""

from proxytool_redux.benchmark import run_all_benchmarks
from proxytool_redux.bootstrap import load_redux4_core, load_redux4_module
from proxytool_redux.scoring import contrastive_adjust, rank_fraction, winsor_bounds

__all__ = [
    "contrastive_adjust",
    "rank_fraction",
    "winsor_bounds",
    "load_redux4_core",
    "load_redux4_module",
    "run_all_benchmarks",
]
