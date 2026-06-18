"""Load REDUX_4 definitions extracted from the full notebook."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional

_CORE_PATH = Path(__file__).resolve().parent / "_extracted" / "redux4_core.py"

# REDUX_4 archival cell eadacf38 is a no-op; patch cell still expects these (from REDUX_3).
_FAMILY_SCORING_SHIM = """
FAMILY_FEATURE_PREFIXES = {
    "commitsem": ("sem_",),
    "contributors": ("contrib_",),
    "churn_cochange": ("churn_", "lines_", "net_", "cochg_"),
    "temporal": ("temp_",),
    "attach": ("attach_rate", "issue_breadth"),
    "embedding": ("emb_",),
}
FAMILY_TO_WEIGHT_KEY = {
    "commitsem": "commitsem",
    "contributors": "contributors",
    "churn_cochange": "cochange",
    "temporal": "temporal",
    "attach": "attach",
    "embedding": "embedding",
}

def _keys_for_family(feature_keys, family):
    prefixes = FAMILY_FEATURE_PREFIXES.get(family, ())
    out = []
    for k in feature_keys:
        if any((isinstance(p, str) and k.startswith(p)) or (k == p) for p in prefixes):
            out.append(k)
    return out

def _safe_cosine_from_keys(q_vec, c_vec, keys):
    if not keys:
        return 0.0
    qa = [float(q_vec.get(k, 0.0)) for k in keys]
    ca = [float(c_vec.get(k, 0.0)) for k in keys]
    return cosine(qa, ca)
"""


def _patch_missing_family_helpers(ns: Dict[str, Any]) -> None:
    if "FAMILY_FEATURE_PREFIXES" in ns:
        return
    exec(compile(_FAMILY_SCORING_SHIM, "<family_scoring_shim>", "exec"), ns)  # noqa: S102


def load_redux4_core(namespace: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute redux4_core.py and return the resulting globals dict."""
    if not _CORE_PATH.is_file():
        raise FileNotFoundError(
            f"Missing {_CORE_PATH}; run: python scripts/extract_redux4_core.py"
        )
    mod_name = "proxytool_redux.redux4_core"
    mod = ModuleType(mod_name)
    mod.__file__ = str(_CORE_PATH)
    ns: Dict[str, Any] = mod.__dict__
    if namespace:
        ns.update(namespace)
    # Allow REPRO notebook to inject token before core reads token.txt / .env
    if namespace and namespace.get("github_token"):
        ns["github_token"] = namespace["github_token"]
    sys.modules[mod_name] = mod
    code = _CORE_PATH.read_text(encoding="utf-8")
    exec(compile(code, str(_CORE_PATH), "exec"), ns)  # noqa: S102
    _patch_missing_family_helpers(ns)
    ns["RUN_SLOW_TESTS"] = False
    return ns


def load_redux4_module() -> ModuleType:
    """Load extracted core as a module (for ``import proxytool_redux.redux4_core`` style access)."""
    name = "proxytool_redux.redux4_core"
    mod = ModuleType(name)
    mod.__file__ = str(_CORE_PATH)
    sys.modules[name] = mod
    load_redux4_core(mod.__dict__)
    return mod
