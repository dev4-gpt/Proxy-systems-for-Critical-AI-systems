#!/usr/bin/env python3
"""
Pick best experiment; write runs/experiments/WINNER.md.
Includes all archived runs. Notes whether winner beats champion (penalty100_min700_cap21).
"""

from __future__ import annotations

import csv
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metamatch_experiment_score import (
    beats_row,
    hub_final30,
    int_val,
    magnet_final30_sum,
    row_by_id,
    score_row,
)

ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = ROOT / "runs" / "experiments"
SUMMARY = EXP_ROOT / "experiment_comparison_summary.csv"
CHAMPION = "penalty100_min700_cap21"
CHAMPION_WEAK_CAP = 3  # allow at most champion Weak + 1


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    if not SUMMARY.exists():
        print(f"Missing {SUMMARY}. Run compare_experiments first.")
        return 1

    rows = read_csv(SUMMARY)
    champion = row_by_id(rows, CHAMPION)
    champ_weak = int_val(champion, "Weak", 2) if champion else 2
    max_weak = champ_weak + 1

    ranked = sorted(rows, key=lambda r: score_row(r, max_weak))
    winner = ranked[0]
    beats_champion = bool(champion and beats_row(winner, champion, max_weak))

    lines = [
        "# MetaMatch experiment winner",
        "",
        f"**Champion (prior best):** `{CHAMPION}`",
    ]
    if champion:
        lines.append(
            f"- TotalMagnetsInTop5={champion.get('TotalMagnetsInTop5')}, "
            f"Weak={champion.get('Weak')}, "
            f"final30 magnet sum={magnet_final30_sum(champion)}"
        )
    lines.extend([
        "",
        f"**Best in comparison table:** `{winner.get('experiment_id')}`",
        f"**Beats champion:** {'yes' if beats_champion else 'no'}",
        "",
        "## Full scorecard (lower is better)",
        "",
        "| experiment_id | penalty | min | cap | Top5 mag | Weak | Good | OK | L/K/S f30 | f30 sum |",
        "|---------------|---------|-----|-----|----------|------|------|-----|-----------|---------|",
    ])
    for r in ranked:
        cap = f"{int_val(r, 'MaxPerOwner')}/{int_val(r, 'MaxPerOwnerPerSubdomain')}"
        l, k, s = hub_final30(r)
        mark = ""
        if r.get("experiment_id") == CHAMPION:
            mark = " (champion)"
        elif r.get("experiment_id") == winner.get("experiment_id") and beats_champion:
            mark = " **"
        lines.append(
            f"| {r.get('experiment_id')}{mark} | {r.get('CrossAnchorFreqPenaltyWeight', '')} | "
            f"{r.get('MinimumScore', '')} | {cap} | {r.get('TotalMagnetsInTop5', '')} | "
            f"{r.get('Weak', '')} | {r.get('Good', '')} | {r.get('OK', '')} | "
            f"{l}/{k}/{s} | {magnet_final30_sum(r)} |"
        )

    apply_id = winner.get("experiment_id") if beats_champion else CHAMPION
    apply_row = row_by_id(rows, apply_id) or winner
    lines.extend([
        "",
        "## Recommended defaults for Get-AnchorMatches.ps1",
        "",
        f"Use: **`{apply_id}`**"
        + (" (new grid winner)" if beats_champion else " (keep champion — grid did not beat it)"),
        "",
        f"- CrossAnchorFreqPenaltyWeight: {apply_row.get('CrossAnchorFreqPenaltyWeight', '100')}",
        f"- MinimumScore: {apply_row.get('MinimumScore', '700')}",
        f"- MaxPerOwner: {apply_row.get('MaxPerOwner', '2')}",
        f"- MaxPerOwnerPerSubdomain: {apply_row.get('MaxPerOwnerPerSubdomain', '1')}",
        "- AllowFallbackFill: true",
        "",
        "## Next phase",
        "",
    ])
    lightning = int_val(apply_row, "MagnetFinal30_pytorch-lightning", 12)
    if lightning >= 11:
        lines.append(
            "If Lightning/Keras/Streamlit stay high in final 30, tune per-anchor GitHub queries "
            "(gradio, streamlit, EasyOCR) — penalty/min/caps alone may plateau."
        )
    else:
        lines.append(
            "Run REDUX similarity on the winning archive when proxy lists are stable "
            "(see REDUX_REPRO.md)."
        )

    out = EXP_ROOT / "WINNER.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(
        f"Best: {winner.get('experiment_id')} (Top5={winner.get('TotalMagnetsInTop5')}, "
        f"Weak={winner.get('Weak')}); beats {CHAMPION}: {beats_champion}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
