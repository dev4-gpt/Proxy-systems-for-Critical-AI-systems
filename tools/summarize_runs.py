#!/usr/bin/env python3
"""
MetaMatch 2.0 - Cross-anchor run summarizer

Why this exists
---------------
When you run multiple anchors, some candidates act like "magnets" (they appear in many anchors).
This script aggregates ranked_matches.csv across runs/manual-ml-py/** and writes a stable set of summaries
to runs/_summaries/. These summaries help you:
  - see top-k per anchor,
  - detect recurring candidates across anchors,
  - build optional diversity penalties.

Usage:
  python tools/summarize_runs.py --runs-dir runs/manual-ml-py --topk 10
  python tools/summarize_runs.py --evaluate   # also run tools/evaluate_anchor_runs.py

Outputs (under runs/_summaries/):
  - top{K}_per_anchor.csv              from ranked_matches (retrieval pool)
  - candidate_frequency_ranked_pool.csv  frequency in full ranked pools (legacy name kept too)
  - top{K}_final30_per_anchor.csv        from 30_Matches (final proxy lists)
  - candidate_frequency_final30.csv      frequency in final 30 only
"""

from __future__ import annotations
import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def read_csv(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default="runs/manual-ml-py", help="Root directory containing per-anchor run folders")
    ap.add_argument("--topk", type=int, default=10, help="Top-K rows to keep per anchor for topk outputs")
    ap.add_argument("--out-dir", default="runs/_summaries", help="Where to write summary files")
    ap.add_argument(
        "--evaluate",
        action="store_true",
        help="After summarizing, run tools/evaluate_anchor_runs.py for anchor_evaluation.csv etc.",
    )
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ranked_files = sorted(runs_dir.rglob("ranked_matches.csv"))

    all_rows: List[dict] = []
    topk_rows: List[dict] = []
    freq: Dict[str, int] = {}

    for rf in ranked_files:
        try:
            rows = read_csv(rf)
        except Exception:
            continue

        # Determine anchor from file content (preferred) or folder name (fallback)
        anchor_name = None
        if rows and rows[0].get("AnchorRepo"):
            anchor_name = rows[0]["AnchorRepo"]
        else:
            anchor_name = rf.parent.name

        # Sort by score descending if present
        def score_val(r: dict) -> float:
            try:
                return float(r.get("Score", "0") or "0")
            except Exception:
                return 0.0

        rows_sorted = sorted(rows, key=score_val, reverse=True)

        for r in rows_sorted:
            r2 = dict(r)
            r2["_anchor_folder"] = rf.parent.name
            r2["_anchor"] = anchor_name
            all_rows.append(r2)

            cand = r.get("CandidateRepo") or r.get("Candidate") or r.get("candidate_repo") or ""
            cand = cand.strip()
            if cand:
                freq[cand] = freq.get(cand, 0) + 1

        for r in rows_sorted[: args.topk]:
            r2 = dict(r)
            r2["_anchor_folder"] = rf.parent.name
            r2["_anchor"] = anchor_name
            topk_rows.append(r2)

    write_csv(out_dir / "ranked_matches_all.csv", all_rows)
    write_csv(out_dir / f"top{args.topk}_per_anchor.csv", topk_rows)

    # Frequency in full ranked pools (misleading legacy filename kept for compatibility)
    freq_rows = [
        {"CandidateRepo": k, "Frequency": v, "Source": "ranked_matches_full_pool"}
        for k, v in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    write_csv(out_dir / f"candidate_frequency_top{args.topk}.csv", freq_rows)
    write_csv(out_dir / "candidate_frequency_ranked_pool.csv", freq_rows)

    # Final 30_Matches: top-K per anchor + cross-anchor frequency (what you use for proxies)
    final30_files = sorted(runs_dir.glob("*/30_Matches.csv"))
    final30_topk_rows: List[dict] = []
    final30_freq: Dict[str, int] = {}
    n_final_anchors = 0

    for ff in final30_files:
        try:
            rows = read_csv(ff)
        except Exception:
            continue
        if not rows:
            continue
        n_final_anchors += 1
        anchor_name = rows[0].get("AnchorRepo") or ff.parent.name

        def rank_val(r: dict) -> int:
            try:
                return int(r.get("Rank") or 999)
            except (TypeError, ValueError):
                return 999

        rows_sorted = sorted(rows, key=rank_val)
        for r in rows_sorted:
            cand = (r.get("CandidateRepo") or "").strip()
            if cand:
                final30_freq[cand] = final30_freq.get(cand, 0) + 1

        for r in rows_sorted[: args.topk]:
            r2 = dict(r)
            r2["_anchor_folder"] = ff.parent.name
            r2["_anchor"] = anchor_name
            r2["_source"] = "30_Matches"
            final30_topk_rows.append(r2)

    write_csv(out_dir / f"top{args.topk}_final30_per_anchor.csv", final30_topk_rows)
    final30_freq_rows = [
        {
            "CandidateRepo": k,
            "Frequency": v,
            "PctOfAnchors": round(100.0 * v / n_final_anchors, 1) if n_final_anchors else 0,
            "Source": "30_Matches_final",
        }
        for k, v in sorted(final30_freq.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    write_csv(out_dir / "candidate_frequency_final30.csv", final30_freq_rows)

    # Collect manifests if present
    manifest_files = sorted(runs_dir.rglob("run_manifest.json"))
    jsonl_path = out_dir / "run_manifests_all.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for mf in manifest_files:
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
            except Exception:
                continue
            data["_path"] = str(mf)
            f.write(json.dumps(data) + "\n")

    print(f"Wrote summaries to: {out_dir}")
    print(f"Anchors (ranked pool): {len(set([r.get('_anchor_folder','') for r in all_rows]))}")
    print(f"Anchors (final 30):     {n_final_anchors}")
    print(f"Total ranked rows: {len(all_rows)}")

    if args.evaluate:
        import subprocess
        import sys

        eval_script = Path(__file__).resolve().parent / "evaluate_anchor_runs.py"
        subprocess.run(
            [sys.executable, str(eval_script), "--runs-dir", str(runs_dir), "--out-dir", str(out_dir)],
            check=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())