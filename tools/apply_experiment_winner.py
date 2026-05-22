#!/usr/bin/env python3
"""Apply winning hyperparameters to Get-AnchorMatches.ps1 and metamatch_hyperparams.json."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "runs" / "experiments" / "experiment_comparison_summary.csv"
MATCHER = ROOT / "Get-AnchorMatches.ps1"
HYPER = ROOT / "metamatch_hyperparams.json"
BASELINE = "penalty55_min700_cap21"


def score_row(row: dict, baseline_weak: int) -> tuple:
    weak = int(float(row.get("Weak") or 99))
    if weak > baseline_weak + 1:
        return (9999, 9999, 9999, row.get("experiment_id", ""))
    return (
        int(float(row.get("TotalMagnetsInTop5") or 9999)),
        sum(int(float(row.get(k) or 0)) for k in row if k.startswith("MagnetFinal30_")),
        weak,
        row.get("experiment_id", ""),
    )


def pick_winner(rows: list[dict]) -> dict:
    baseline_weak = 5
    for r in rows:
        if r.get("experiment_id") == BASELINE:
            baseline_weak = int(float(r.get("Weak") or 5))
            break
    candidates = [r for r in rows if r.get("experiment_id") != "penalty30_min700_cap21"]
    return sorted(candidates, key=lambda r: score_row(r, baseline_weak))[0]


def patch_ps1(w: dict) -> None:
    text = MATCHER.read_text(encoding="utf-8")
    penalty = float(w.get("CrossAnchorFreqPenaltyWeight") or 55)
    minimum = int(float(w.get("MinimumScore") or 700))
    max_owner = int(float(w.get("MaxPerOwner") or 2))
    max_sub = int(float(w.get("MaxPerOwnerPerSubdomain") or 1))
    allow_fallback = "penalty55_min700_cap21_nofallback" not in w.get("experiment_id", "")

    text = re.sub(
        r"(\[double\]\$CrossAnchorFreqPenaltyWeight\s*=\s*)[\d.]+",
        rf"\g<1>{penalty}",
        text,
        count=1,
    )
    text = re.sub(
        r"(\[int\]\$MinimumScore\s*=\s*)\d+",
        rf"\g<1>{minimum}",
        text,
        count=1,
    )
    text = re.sub(
        r"(\[int\]\$MaxPerOwner\s*=\s*)\d+",
        rf"\g<1>{max_owner}",
        text,
        count=1,
    )
    text = re.sub(
        r"(\[int\]\$MaxPerOwnerPerSubdomain\s*=\s*)\d+",
        rf"\g<1>{max_sub}",
        text,
        count=1,
    )
    text = re.sub(
        r"(\[switch\]\$AllowFallbackFill\s*=\s*)\$(true|false)",
        rf"\g<1>${'true' if allow_fallback else 'false'}",
        text,
        count=1,
    )
    MATCHER.write_text(text, encoding="utf-8")


def write_json(w: dict) -> None:
    payload = {
        "CrossAnchorFreqPenaltyWeight": float(w.get("CrossAnchorFreqPenaltyWeight") or 55),
        "MinimumScore": int(float(w.get("MinimumScore") or 700)),
        "MaxPerOwner": int(float(w.get("MaxPerOwner") or 2)),
        "MaxPerOwnerPerSubdomain": int(float(w.get("MaxPerOwnerPerSubdomain") or 1)),
        "AllowFallbackFill": "penalty55_min700_cap21_nofallback" not in w.get("experiment_id", ""),
        "winner_experiment_id": w.get("experiment_id"),
    }
    HYPER.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if not SUMMARY.exists():
        print(f"Missing {SUMMARY}")
        return 1
    rows = list(csv.DictReader(SUMMARY.open(encoding="utf-8")))
    winner = pick_winner(rows)
    patch_ps1(winner)
    write_json(winner)
    print(f"Applied winner {winner.get('experiment_id')} to {MATCHER.name} and {HYPER.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
