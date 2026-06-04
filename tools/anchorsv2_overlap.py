#!/usr/bin/env python3
"""Compare top-k proxy overlap between queryv2 and anchorsv2 experiment archives."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Set


def top_repos(matches_csv: Path, k: int) -> List[str]:
    rows: List[tuple[int, str]] = []
    with matches_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                rank = int(float(row.get("Rank", "999")))
            except ValueError:
                continue
            if rank <= k:
                rows.append((rank, row.get("CandidateRepo", "")))
    rows.sort(key=lambda x: x[0])
    return [r for _, r in rows if r]


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queryv2",
        default="runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py",
    )
    parser.add_argument(
        "--anchorsv2",
        default="runs/experiments/penalty300_min700_cap22_anchorsv2/manual-ml-py",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--output",
        default="results_benchmark/anchorsv2_overlap.csv",
    )
    args = parser.parse_args()

    qbase = Path(args.queryv2)
    abase = Path(args.anchorsv2)
    out_rows: List[Dict[str, object]] = []

    q_dirs = {p.name: p for p in qbase.iterdir() if p.is_dir()}
    a_dirs = {p.name: p for p in abase.iterdir() if p.is_dir()}

    for slug in sorted(set(q_dirs) & set(a_dirs)):
        qpath = q_dirs[slug] / "30_Matches.csv"
        apath = a_dirs[slug] / "30_Matches.csv"
        if not qpath.is_file() or not apath.is_file():
            continue
        q_anchor = ""
        a_anchor = ""
        with qpath.open(encoding="utf-8", newline="") as fh:
            r = next(csv.DictReader(fh), None)
            if r:
                q_anchor = r.get("AnchorRepo", "")
        with apath.open(encoding="utf-8", newline="") as fh:
            r = next(csv.DictReader(fh), None)
            if r:
                a_anchor = r.get("AnchorRepo", "")

        qset = set(top_repos(qpath, args.top_k))
        aset = set(top_repos(apath, args.top_k))
        out_rows.append(
            {
                "folder_slug": slug,
                "queryv2_anchor": q_anchor,
                "anchorsv2_anchor": a_anchor,
                "same_anchor_repo": q_anchor == a_anchor,
                "topk": args.top_k,
                "shared_proxies": len(qset & aset),
                "jaccard_topk": round(jaccard(qset, aset), 4),
                "queryv2_top5": " | ".join(sorted(qset)),
                "anchorsv2_top5": " | ".join(sorted(aset)),
            }
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()) if out_rows else [])
        if out_rows:
            writer.writeheader()
            writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} overlap rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
