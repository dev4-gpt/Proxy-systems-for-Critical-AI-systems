#!/usr/bin/env python3
"""Refresh EXPERIMENT_LOG.md from experiment_comparison_summary.csv (all experiments, ranked)."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metamatch_experiment_score import int_val, score_row

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "runs" / "experiments" / "experiment_comparison_summary.csv"
LOG = ROOT / "runs" / "experiments" / "EXPERIMENT_LOG.md"
CHAMPION = "penalty100_min700_cap21"


def params_str(r: dict) -> str:
    return (
        f"penalty={r.get('CrossAnchorFreqPenaltyWeight', '')}, "
        f"min={r.get('MinimumScore', '')}, "
        f"cap={int_val(r, 'MaxPerOwner')}/{int_val(r, 'MaxPerOwnerPerSubdomain')}"
    )


def main() -> None:
    if not SUMMARY.exists():
        return
    rows = list(csv.DictReader(SUMMARY.open(encoding="utf-8")))
    champ = next((r for r in rows if r.get("experiment_id") == CHAMPION), None)
    max_weak = int_val(champ, "Weak", 2) + 1 if champ else 99
    ranked = sorted(rows, key=lambda r: score_row(r, max_weak))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# MetaMatch experiment log",
        "",
        f"Champion reference: `{CHAMPION}`. Sorted by magnet score (lower is better).",
        "",
        "| Date | experiment_id | Params | Top5 mag | Weak | Good | OK | Notes |",
        "|------|---------------|--------|----------|------|------|-----|-------|",
    ]
    for r in ranked:
        eid = r.get("experiment_id", "")
        note = "champion" if eid == CHAMPION else "archived"
        lines.append(
            f"| {today} | {eid} | {params_str(r)} | {r.get('TotalMagnetsInTop5', '')} | "
            f"{r.get('Weak', '')} | {r.get('Good', '')} | {r.get('OK', '')} | {note} |"
        )
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {LOG} ({len(ranked)} experiments)")


if __name__ == "__main__":
    main()
