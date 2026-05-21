#!/usr/bin/env python3
"""
Compare two archived MetaMatch experiments under runs/experiments/<name>/.

Writes:
  - experiment_comparison_summary.csv   one row per experiment (aggregate metrics)
  - anchor_comparison_by_experiment.csv   one row per anchor per experiment
  - magnet_comparison_final30.csv         key magnets: frequency in final 30 per experiment

Usage:
  python tools/compare_experiments.py \\
    --experiments penalty30_min700_cap21 penalty55_min700_cap21
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

MAGNETS = frozenset({
    "Lightning-AI/pytorch-lightning",
    "keras-team/keras",
    "huggingface/transformers",
    "ray-project/ray",
    "d2l-ai/d2l-zh",
    "pytorch/pytorch",
    "scikit-learn/scikit-learn",
    "explosion/spaCy",
    "streamlit/streamlit",
    "gradio-app/gradio",
    "microsoft/qlib",
    "roboflow/supervision",
    "deepspeedai/DeepSpeed",
    "eriklindernoren/ML-From-Scratch",
    "recommenders-team/recommenders",
})

KEY_MAGNETS = [
    "Lightning-AI/pytorch-lightning",
    "keras-team/keras",
    "streamlit/streamlit",
    "gradio-app/gradio",
    "explosion/spaCy",
    "d2l-ai/d2l-zh",
]


def read_csv(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: List[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load_hyperparams(exp_dir: Path) -> dict:
    hp_path = exp_dir / "run_hyperparams.csv"
    rows = read_csv(hp_path)
    if not rows:
        return {}
    r = rows[0]
    for row in rows:
        if row.get("CrossAnchorFreqPenaltyWeight"):
            r = row
            break
    return {
        "MinimumScore": r.get("MinimumScore", ""),
        "CrossAnchorFreqPenaltyWeight": r.get("CrossAnchorFreqPenaltyWeight", ""),
        "MaxPerOwner": r.get("MaxPerOwner", ""),
        "MaxPerOwnerPerSubdomain": r.get("MaxPerOwnerPerSubdomain", ""),
    }


def experiment_metrics(exp_dir: Path) -> dict:
    eval_rows = read_csv(exp_dir / "anchor_evaluation.csv")
    mag_freq = read_csv(exp_dir / "magnet_frequency_final30.csv")
    hp = load_hyperparams(exp_dir)

    ratings = {"Good": 0, "OK": 0, "Weak": 0}
    magnets_top5_total = 0
    for row in eval_rows:
        rat = row.get("Rating", "")
        if rat in ratings:
            ratings[rat] += 1
        try:
            magnets_top5_total += int(row.get("MagnetsInTop5") or 0)
        except ValueError:
            pass

    freq_map = {r["CandidateRepo"]: int(r.get("FrequencyInFinal30") or r.get("Frequency") or 0)
                for r in mag_freq if r.get("CandidateRepo")}

    out = {
        **hp,
        "AnchorsEvaluated": len(eval_rows),
        "Good": ratings["Good"],
        "OK": ratings["OK"],
        "Weak": ratings["Weak"],
        "TotalMagnetsInTop5": magnets_top5_total,
    }
    for m in KEY_MAGNETS:
        short = m.split("/")[-1]
        out[f"MagnetFinal30_{short}"] = freq_map.get(m, 0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--experiments",
        nargs="+",
        required=True,
        help="Experiment folder names under runs/experiments/",
    )
    ap.add_argument("--experiments-root", default="runs/experiments")
    ap.add_argument("--out-dir", default="runs/experiments")
    args = ap.parse_args()

    root = Path(args.experiments_root)
    out_dir = Path(args.out_dir)

    summary_rows: List[dict] = []
    anchor_rows: List[dict] = []

    for exp_id in args.experiments:
        exp_dir = root / exp_id
        if not exp_dir.is_dir():
            print(f"Warning: missing experiment dir: {exp_dir}")
            continue

        meta_path = exp_dir / "experiment_meta.json"
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        m = experiment_metrics(exp_dir)
        summary_rows.append({
            "experiment_id": exp_id,
            "description": meta.get("description", ""),
            "archived_at": meta.get("archived_at", ""),
            **m,
        })

        for row in read_csv(exp_dir / "anchor_evaluation.csv"):
            anchor_rows.append({
                "experiment_id": exp_id,
                "AnchorRepo": row.get("AnchorRepo", ""),
                "Rating": row.get("Rating", ""),
                "MagnetsInTop5": row.get("MagnetsInTop5", ""),
                "MagnetsInTop10": row.get("MagnetsInTop10", ""),
                "MagnetsInFinal30": row.get("MagnetsInFinal30", ""),
                "QualifiedInFinal30": row.get("QualifiedInFinal30", ""),
                "Top1_CandidateRepo": row.get("Top1_CandidateRepo", ""),
                "Top5_Candidates": row.get("Top5_Candidates", ""),
            })

    magnet_rows: List[dict] = []
    exp_ids = [r["experiment_id"] for r in summary_rows]

    freq_by_exp: Dict[str, Dict[str, int]] = {}
    for exp_id in exp_ids:
        exp_dir = root / exp_id
        freq_by_exp[exp_id] = {}
        for row in read_csv(exp_dir / "magnet_frequency_final30.csv"):
            c = row.get("CandidateRepo", "")
            if c:
                try:
                    freq_by_exp[exp_id][c] = int(row.get("FrequencyInFinal30") or 0)
                except ValueError:
                    freq_by_exp[exp_id][c] = 0

    candidates = set(KEY_MAGNETS)
    for fmap in freq_by_exp.values():
        for c, v in fmap.items():
            if c in MAGNETS and v > 0:
                candidates.add(c)

    for cand in sorted(candidates):
        row = {"CandidateRepo": cand, "IsMagnet": cand in MAGNETS}
        for exp_id in exp_ids:
            row[f"{exp_id}_Final30Freq"] = freq_by_exp.get(exp_id, {}).get(cand, 0)
        if len(exp_ids) == 2:
            a, b = exp_ids
            row["Delta_Final30Freq"] = row[f"{b}_Final30Freq"] - row[f"{a}_Final30Freq"]
        magnet_rows.append(row)

    write_csv(out_dir / "experiment_comparison_summary.csv", summary_rows)
    write_csv(out_dir / "anchor_comparison_by_experiment.csv", anchor_rows)
    write_csv(out_dir / "magnet_comparison_final30.csv", magnet_rows)

    print(f"Wrote comparison tables to {out_dir}/")
    for r in summary_rows:
        print(
            f"  {r['experiment_id']}: penalty={r.get('CrossAnchorFreqPenaltyWeight')} "
            f"Good={r.get('Good')} OK={r.get('OK')} Weak={r.get('Weak')} "
            f"Lightning={r.get('MagnetFinal30_pytorch-lightning', '')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
