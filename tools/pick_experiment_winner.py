#!/usr/bin/env python3
"""
Pick best experiment from runs/experiments/*/anchor_evaluation.csv archives.
Writes runs/experiments/WINNER.md and prints recommendation.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = ROOT / "runs" / "experiments"
SUMMARY = EXP_ROOT / "experiment_comparison_summary.csv"
BASELINE = "penalty55_min700_cap21"
GUARD_MAX_WEAK = 6  # must not be worse than penalty55 by more than 1


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def int_val(row: dict, key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key) or default))
    except (TypeError, ValueError):
        return default


def float_val(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key) or default)
    except (TypeError, ValueError):
        return default


def magnet_final30_sum(row: dict) -> int:
    keys = [k for k in row if k.startswith("MagnetFinal30_")]
    return sum(int_val(row, k) for k in keys)


def score_row(row: dict, baseline_weak: int) -> tuple:
    """Lower is better for sorting (we negate for max)."""
    weak = int_val(row, "Weak")
    if weak > baseline_weak + 1:
        return (9999, 9999, 9999, row.get("experiment_id", ""))
    mtop5 = int_val(row, "TotalMagnetsInTop5")
    m30 = magnet_final30_sum(row)
    weak_pen = weak
    return (mtop5, m30, weak_pen, row.get("experiment_id", ""))


def main() -> int:
    if not SUMMARY.exists():
        print(f"Missing {SUMMARY}. Run compare_experiments first.")
        return 1

    rows = read_csv(SUMMARY)
    baseline_weak = 5
    for r in rows:
        if r.get("experiment_id") == BASELINE:
            baseline_weak = int_val(r, "Weak", 5)
            break

    candidates = [r for r in rows if r.get("experiment_id") != "penalty30_min700_cap21"]
    if not candidates:
        print("No candidate experiments.")
        return 1

    ranked = sorted(candidates, key=lambda r: score_row(r, baseline_weak))
    winner = ranked[0]

    lines = [
        "# MetaMatch sweep winner",
        "",
        f"**Recommended experiment:** `{winner.get('experiment_id')}`",
        "",
        "## Scorecard (lower is better)",
        "",
        "| experiment_id | TotalMagnetsInTop5 | Weak | Good | OK | Lightning final30 | Keras | Streamlit |",
        "|---------------|-------------------|------|------|-----|-------------------|-------|-----------|",
    ]
    for r in ranked:
        lines.append(
            f"| {r.get('experiment_id')} | {r.get('TotalMagnetsInTop5')} | {r.get('Weak')} | "
            f"{r.get('Good')} | {r.get('OK')} | {r.get('MagnetFinal30_pytorch-lightning', '')} | "
            f"{r.get('MagnetFinal30_keras', '')} | {r.get('MagnetFinal30_streamlit', '')} |"
        )

    w = winner
    lines.extend([
        "",
        "## Suggested defaults for Get-AnchorMatches.ps1",
        "",
        f"- CrossAnchorFreqPenaltyWeight: {w.get('CrossAnchorFreqPenaltyWeight', '55')}",
        f"- MinimumScore: {w.get('MinimumScore', '700')}",
        f"- MaxPerOwner: {w.get('MaxPerOwner', '2')}",
        f"- MaxPerOwnerPerSubdomain: {w.get('MaxPerOwnerPerSubdomain', '1')}",
        "",
        "## Next phase",
        "",
    ])

    lightning = int_val(w, "MagnetFinal30_pytorch-lightning", 12)
    if lightning >= 12:
        lines.append(
            "Top hubs (Lightning/Keras/Streamlit) still at 12/20 in final 30 — "
            "consider anchor-specific GitHub queries for gradio, streamlit, EasyOCR."
        )
    else:
        lines.append("Magnet final-30 counts improved vs penalty55; proceed to professor review / REDUX on Good anchors.")

    out = EXP_ROOT / "WINNER.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Winner: {winner.get('experiment_id')} "
          f"(TotalMagnetsInTop5={winner.get('TotalMagnetsInTop5')}, Weak={winner.get('Weak')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
