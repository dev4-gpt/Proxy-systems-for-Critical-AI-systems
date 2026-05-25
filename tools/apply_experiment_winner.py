#!/usr/bin/env python3
"""Apply winning hyperparameters only if result beats penalty100_min700_cap21."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metamatch_experiment_score import beats_row, row_by_id, score_row

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "runs" / "experiments" / "experiment_comparison_summary.csv"
MATCHER = ROOT / "Get-AnchorMatches.ps1"
HYPER = ROOT / "metamatch_hyperparams.json"
CHAMPION = "penalty100_min700_cap21"


def pick_apply_row(rows: list[dict]) -> tuple[dict, bool]:
    champion = row_by_id(rows, CHAMPION)
    if not champion:
        ranked = sorted(rows, key=lambda r: score_row(r, 99))
        return ranked[0], True
    champ_weak = int(float(champion.get("Weak") or 2))
    ranked = sorted(rows, key=lambda r: score_row(r, champ_weak + 1))
    best = ranked[0]
    if beats_row(best, champion, champ_weak + 1):
        return best, True
    return champion, False


def patch_ps1(w: dict) -> None:
    text = MATCHER.read_text(encoding="utf-8")
    penalty = float(w.get("CrossAnchorFreqPenaltyWeight") or 100)
    minimum = int(float(w.get("MinimumScore") or 700))
    max_owner = int(float(w.get("MaxPerOwner") or 2))
    max_sub = int(float(w.get("MaxPerOwnerPerSubdomain") or 1))
    allow_fallback = "nofallback" not in w.get("experiment_id", "")

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


def write_json(w: dict, beats: bool) -> None:
    payload = {
        "CrossAnchorFreqPenaltyWeight": float(w.get("CrossAnchorFreqPenaltyWeight") or 100),
        "MinimumScore": int(float(w.get("MinimumScore") or 700)),
        "MaxPerOwner": int(float(w.get("MaxPerOwner") or 2)),
        "MaxPerOwnerPerSubdomain": int(float(w.get("MaxPerOwnerPerSubdomain") or 1)),
        "AllowFallbackFill": "nofallback" not in w.get("experiment_id", ""),
        "winner_experiment_id": w.get("experiment_id"),
        "beats_champion_penalty100_min700_cap21": beats,
        "champion_experiment_id": CHAMPION,
    }
    HYPER.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if not SUMMARY.exists():
        print(f"Missing {SUMMARY}")
        return 1
    rows = list(csv.DictReader(SUMMARY.open(encoding="utf-8")))
    apply_row, beats = pick_apply_row(rows)
    patch_ps1(apply_row)
    write_json(apply_row, beats)
    note = "beat" if beats else "did not beat"
    print(f"Applied {apply_row.get('experiment_id')} ({note} {CHAMPION})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
