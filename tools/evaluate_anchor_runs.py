#!/usr/bin/env python3
"""
Evaluate MetaMatch per-anchor runs from 30_Matches.csv (final proxy lists).

Writes tables under runs/_summaries/:
  - anchor_evaluation.csv       one row per anchor (quality metrics)
  - anchor_top5_matches.csv     top 5 per anchor (long format)
  - magnet_frequency_final30.csv  how often each candidate appears in final 30 across anchors
  - run_hyperparams.csv         params from run_manifest.json per anchor

Usage:
  python tools/evaluate_anchor_runs.py --runs-dir runs/manual-ml-py
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

# Known cross-anchor magnets (generic ML hubs)
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


def read_csv(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def score_float(r: dict, key: str = "Score") -> float:
    try:
        return float(r.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def is_qualified(r: dict) -> bool:
    return str(r.get("Qualified", "")).strip().lower() == "true"


def rate_anchor(mag_top5: int, qual_count: int, anchor: str) -> str:
    if "OpenBB" in anchor and qual_count < 5:
        return "Weak"
    if mag_top5 >= 3:
        return "Weak"
    if mag_top5 == 2:
        return "OK"
    return "Good"


def load_manifest(folder: Path) -> Optional[dict]:
    mf = folder / "run_manifest.json"
    if not mf.exists():
        return None
    try:
        return json.loads(mf.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default="runs/manual-ml-py")
    ap.add_argument("--out-dir", default="runs/_summaries")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    match_files = sorted(runs_dir.glob("*/30_Matches.csv"))
    if not match_files:
        print(f"No 30_Matches.csv under {runs_dir}")
        return 1

    n_anchors = len(match_files)
    eval_rows: List[dict] = []
    top5_rows: List[dict] = []
    hyper_rows: List[dict] = []
    final30_freq: Dict[str, int] = {}

    for mf in match_files:
        rows = read_csv(mf)
        if not rows:
            continue

        anchor = rows[0].get("AnchorRepo") or mf.parent.name
        folder = mf.parent.name

        ranked_path = mf.parent / "ranked_matches.csv"
        ranked_top10: List[str] = []
        if ranked_path.exists():
            ranked = sorted(read_csv(ranked_path), key=score_float, reverse=True)
            ranked_top10 = [r.get("CandidateRepo", "") for r in ranked[:10]]

        final_sorted = sorted(rows, key=lambda r: int(r.get("Rank") or 999))
        top30 = [r.get("CandidateRepo", "") for r in final_sorted[:30]]
        top10_final = top30[:10]
        top5 = top30[:5]

        for c in top30:
            if c:
                final30_freq[c] = final30_freq.get(c, 0) + 1

        mag5 = sum(1 for c in top5 if c in MAGNETS)
        mag10 = sum(1 for c in top10_final if c in MAGNETS)
        mag30 = sum(1 for c in top30 if c in MAGNETS)
        qual = sum(1 for r in final_sorted if is_qualified(r))

        overlap_summary = len(set(top10_final) & set(ranked_top10)) if ranked_top10 else ""

        pens = []
        for r in final_sorted[:5]:
            try:
                pens.append(float(r.get("PenaltyCrossAnchorFreq") or 0))
            except (TypeError, ValueError):
                pass
        avg_pen = round(sum(pens) / len(pens), 2) if pens else ""

        manifest = load_manifest(mf.parent)
        params = (manifest or {}).get("params") or {}
        hyper_rows.append({
            "AnchorRepo": anchor,
            "_anchor_folder": folder,
            "MinimumScore": params.get("MinimumScore", ""),
            "CrossAnchorFreqPenaltyWeight": params.get("CrossAnchorFreqPenaltyWeight", ""),
            "MaxPerOwner": params.get("MaxPerOwner", ""),
            "MaxPerOwnerPerSubdomain": params.get("MaxPerOwnerPerSubdomain", ""),
            "TopK": params.get("TopK", ""),
            "manifest_path": str(mf.parent / "run_manifest.json") if manifest else "",
        })

        rating = rate_anchor(mag5, qual, anchor)

        eval_rows.append({
            "AnchorRepo": anchor,
            "_anchor_folder": folder,
            "Rating": rating,
            "MagnetsInTop5": mag5,
            "MagnetsInTop10": mag10,
            "MagnetsInFinal30": mag30,
            "QualifiedInFinal30": qual,
            "OverlapFinal10VsRanked10": overlap_summary,
            "RankedPoolSize": len(read_csv(ranked_path)) if ranked_path.exists() else "",
            "AvgPenaltyCrossAnchorTop5": avg_pen,
            "Top1_CandidateRepo": top5[0] if len(top5) > 0 else "",
            "Top2_CandidateRepo": top5[1] if len(top5) > 1 else "",
            "Top3_CandidateRepo": top5[2] if len(top5) > 2 else "",
            "Top4_CandidateRepo": top5[3] if len(top5) > 3 else "",
            "Top5_CandidateRepo": top5[4] if len(top5) > 4 else "",
            "Top5_Candidates": " | ".join(top5),
        })

        for i, r in enumerate(final_sorted[:5], start=1):
            c = r.get("CandidateRepo", "")
            top5_rows.append({
                "AnchorRepo": anchor,
                "_anchor_folder": folder,
                "Rank": r.get("Rank", i),
                "CandidateRepo": c,
                "IsMagnet": c in MAGNETS,
                "Score": r.get("Score", ""),
                "Qualified": r.get("Qualified", ""),
                "PenaltyCrossAnchorFreq": r.get("PenaltyCrossAnchorFreq", ""),
                "FrequencyInFinal30AcrossAnchors": final30_freq.get(c, 0),  # filled below
                "Description": (r.get("Description") or "")[:200],
            })

    # Fix frequency in top5_rows (computed after all anchors)
    for r in top5_rows:
        c = r["CandidateRepo"]
        r["FrequencyInFinal30AcrossAnchors"] = final30_freq.get(c, 0)

    eval_rows.sort(key=lambda x: (x["Rating"], -x["MagnetsInTop5"], x["AnchorRepo"]))
    magnet_freq_rows = [
        {
            "CandidateRepo": k,
            "FrequencyInFinal30": v,
            "PctOfAnchors": round(100.0 * v / n_anchors, 1),
            "IsMagnet": k in MAGNETS,
        }
        for k, v in sorted(final30_freq.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    write_csv(out_dir / "anchor_evaluation.csv", eval_rows)
    write_csv(out_dir / "anchor_top5_matches.csv", top5_rows)
    write_csv(out_dir / "magnet_frequency_final30.csv", magnet_freq_rows)
    write_csv(out_dir / "run_hyperparams.csv", hyper_rows)

    ratings = {}
    for r in eval_rows:
        ratings[r["Rating"]] = ratings.get(r["Rating"], 0) + 1

    print(f"Wrote evaluation tables to: {out_dir}")
    print(f"  anchor_evaluation.csv          ({len(eval_rows)} anchors)")
    print(f"  anchor_top5_matches.csv        ({len(top5_rows)} rows)")
    print(f"  magnet_frequency_final30.csv ({len(magnet_freq_rows)} candidates)")
    print(f"  run_hyperparams.csv            ({len(hyper_rows)} rows)")
    print(f"Ratings: {ratings}")
    top_mags = [r for r in magnet_freq_rows if r["IsMagnet"]][:8]
    if top_mags:
        print("Top magnets in final 30 across anchors:")
        for r in top_mags:
            print(f"  {r['FrequencyInFinal30']}/{n_anchors}  {r['CandidateRepo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
