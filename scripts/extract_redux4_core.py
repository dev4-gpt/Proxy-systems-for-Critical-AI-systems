#!/usr/bin/env python3
"""Re-extract proxytool_REDUX_4.ipynb library + benchmark cells into proxytool_redux/_extracted/redux4_core.py."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "proxytool_REDUX_4.ipynb"
OUT_PATH = ROOT / "proxytool_redux" / "_extracted" / "redux4_core.py"

LIB_INDICES = list(range(8, 57)) + [107, 119, 126, 148, 149, 150, 156, 163]
RUNNER_TAIL_MARKERS = (
    "# A/B: REDUX_3",
    "table_custom_30_weighted = build_custom_30_table",
    "# Table 1 — Known similar",
    "table_test1 = build_argument_table",
)


def _strip_runner_tail(src: str) -> str:
    """Drop notebook 'run now' tails; keep function/class definitions only."""
    for marker in RUNNER_TAIL_MARKERS:
        idx = src.find(marker)
        if idx != -1:
            return src[:idx].rstrip() + "\n"
    return src


def _should_skip_cell(src: str) -> bool:
    stripped = src.strip()
    if not stripped:
        return True
    if "# In Jupyter, do NOT run this cell" in src:
        return True
    if "ARCHIVAL (cell id" in src:
        return True
    if "duplicate patch cell disabled" in src.lower():
        return True
    # CLI entry only — not abstract methods with NotImplementedError
    if 'if __name__ == "__main__"' in src and "ArgumentParser" in src:
        return True
    return False

PREAMBLE = """
# Overrides for extracted REPRO runs (full notebook keeps its own flags).
RUN_SLOW_TESTS = False
"""


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells = nb["cells"]
    parts = [
        '"""Auto-extracted from proxytool_REDUX_4.ipynb — re-run scripts/extract_redux4_core.py."""\n',
        "from __future__ import annotations\n",
        PREAMBLE,
        "\n",
    ]
    for i in LIB_INDICES:
        c = cells[i]
        if c["cell_type"] != "code":
            continue
        src = "".join(c.get("source", []))
        if _should_skip_cell(src):
            continue
        lines = src.splitlines(keepends=True)
        # Drop Jupyter magics; keep the rest of the cell.
        while lines and lines[0].strip().startswith("%"):
            lines.pop(0)
        # Only the bundle header may use __future__ imports.
        while lines and lines[0].strip() in (
            "from __future__ import annotations",
            "from __future__ import annotations\n",
        ):
            lines.pop(0)
        src = "".join(lines)
        src = _strip_runner_tail(src)
        if not src.strip():
            continue
        parts.append(f"\n# --- notebook cell {i} (id={c.get('id')}) ---\n")
        parts.append(src if src.endswith("\n") else src + "\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
