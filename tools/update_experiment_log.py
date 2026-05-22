#!/usr/bin/env python3
"""Refresh EXPERIMENT_LOG.md rows from experiment_comparison_summary.csv."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "runs" / "experiments" / "experiment_comparison_summary.csv"
LOG = ROOT / "runs" / "experiments" / "EXPERIMENT_LOG.md"

ORDER = [
    "penalty30_min700_cap21",
    "penalty55_min700_cap21",
    "penalty75_min700_cap21",
    "penalty100_min700_cap21",
    "penalty55_min750_cap21",
    "penalty55_min700_cap11",
    "penalty55_min700_cap21_nofallback",
]

PARAMS = {
    "penalty30_min700_cap21": "penalty=30, min=700, cap=2/1",
    "penalty55_min700_cap21": "penalty=55, min=700, cap=2/1",
    "penalty75_min700_cap21": "penalty=75, min=700, cap=2/1",
    "penalty100_min700_cap21": "penalty=100, min=700, cap=2/1",
    "penalty55_min750_cap21": "penalty=55, min=750, cap=2/1",
    "penalty55_min700_cap11": "penalty=55, min=700, cap=1/1",
    "penalty55_min700_cap21_nofallback": "penalty=55, min=700, cap=2/1, fallback=off",
}


def main() -> None:
    if not SUMMARY.exists():
        return
    by_id = {r["experiment_id"]: r for r in csv.DictReader(SUMMARY.open(encoding="utf-8"))}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# MetaMatch experiment log",
        "",
        "| Date (UTC) | experiment_id | Params | Ran | Failed | TotalMagnetsInTop5 | Good | OK | Weak | Notes |",
        "|------------|---------------|--------|-----|--------|-------------------|------|-----|------|-------|",
    ]
    for eid in ORDER:
        r = by_id.get(eid, {})
        params = PARAMS.get(eid, "")
        if r:
            lines.append(
                f"| {today} | {eid} | {params} | {r.get('AnchorsEvaluated', '')} | 0 | "
                f"{r.get('TotalMagnetsInTop5', '')} | {r.get('Good', '')} | {r.get('OK', '')} | "
                f"{r.get('Weak', '')} | archived |"
            )
        else:
            lines.append(f"| | {eid} | {params} | | | | | | | |")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {LOG}")


if __name__ == "__main__":
    main()
