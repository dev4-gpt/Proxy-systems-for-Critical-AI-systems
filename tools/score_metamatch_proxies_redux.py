#!/usr/bin/env python3
"""Score anchor→proxy pairs from a frozen MetaMatch experiment archive with REDUX."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

PILOT_ANCHORS = {
    "jina-ai/serve",
    "ray-project/ray",
    "apache/airflow",
    "OpenBB-finance/OpenBB",
}


def slug_from_anchor(anchor_repo: str) -> str:
    return anchor_repo.replace("/", "-")


def read_matches(path: Path, top_k: int) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rank = int(float(row.get("Rank", "999") or 999))
            if rank > top_k:
                continue
            rows.append(row)
    return rows


def collect_anchors(archive: Path, pilot_only: bool) -> List[Path]:
    base = archive / "manual-ml-py"
    dirs = sorted(p for p in base.iterdir() if p.is_dir() and (p / "30_Matches.csv").is_file())
    if not pilot_only:
        return dirs
    out = []
    for d in dirs:
        matches = read_matches(d / "30_Matches.csv", top_k=1)
        if not matches:
            continue
        anchor = matches[0].get("AnchorRepo", "")
        if anchor in PILOT_ANCHORS:
            out.append(d)
    return out


def score_pair(
    query_url: str,
    target_url: str,
    g: Dict[str, object],
    max_commits: int,
    *,
    metadata_only: bool = False,
) -> Dict[str, float]:
    fn = g["_method_score_percent_for_target"]
    token = g.get("github_token")
    scores = fn(
        query_url,
        target_url,
        token=token,
        max_commits=max_commits,
        metadata_weights=g.get("CAIS_WEIGHTS_REDUX3_BLEND"),
        metadata_windows=g.get("REDUX3_METADATA_WINDOWS"),
        metadata_window_weights=g.get("REDUX3_WINDOW_WEIGHTS"),
        normalization_mode="global_minmax",
        pairwise_scoring=True,
        metadata_scoring_mode="family_cosine",
        reporting_mode=g.get("REDUX3_DEFAULT_REPORTING_BENCHMARK", "contrastive"),
        use_domain_hard_negatives=True,
    )
    out = {"metadata_pct": float(scores["Metadata"])}
    if metadata_only:
        return out
    out.update(
        {
            "code_centric_pct": float(scores["Code centric"]),
            "dynamic_pct": float(scores["Dynamic"]),
            "cross_language_pct": float(scores["Cross language"]),
        }
    )
    return out


def anchor_out_csv(out_dir: Path, anchor_repo: str) -> Path:
    return out_dir / f"{slug_from_anchor(anchor_repo)}.csv"


def csv_has_scores(path: Path, min_rows: int) -> bool:
    if not path.is_file():
        return False
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    scored = [r for r in rows if r.get("metadata_pct") not in ("", None)]
    return len(scored) >= min_rows


def write_rollup_from_dir(out_dir: Path, top_k: int) -> int:
    rollup: List[Dict[str, object]] = []
    for path in sorted(out_dir.glob("*.csv")):
        if path.name == "rollup_summary.csv":
            continue
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        anchor = rows[0].get("anchor_repo", path.stem)
        meta = []
        for r in rows:
            val = r.get("metadata_pct")
            if val in ("", None):
                continue
            try:
                meta.append(float(val))
            except ValueError:
                continue
        rollup.append(
            {
                "anchor_repo": anchor,
                "n_pairs": len(rows),
                "metadata_mean_topk": round(sum(meta) / len(meta), 2) if meta else "",
                "metadata_min_topk": round(min(meta), 2) if meta else "",
                "metadata_max_topk": round(max(meta), 2) if meta else "",
                "thin_pool": len(rows) < top_k,
            }
        )
    if not rollup:
        return 0
    rollup_path = out_dir / "rollup_summary.csv"
    with rollup_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rollup[0].keys()))
        writer.writeheader()
        writer.writerows(rollup)
    return len(rollup)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        default="runs/experiments/penalty300_min700_cap22_queryv2",
    )
    parser.add_argument("--output-dir", default="results_benchmark/queryv2_redux")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-commits", type=int, default=80)
    parser.add_argument("--pilot-only", action="store_true")
    parser.add_argument("--fit-global", action="store_true", help="Fit global normalizer on anchor+proxy URLs")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Score metadata only (faster full-cohort rollup)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip anchors whose output CSV already has at least top-k scored rows",
    )
    args = parser.parse_args()

    archive = Path(args.archive)
    if not archive.is_dir():
        raise SystemExit(f"Archive not found: {archive}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    from proxytool_redux.bootstrap import load_redux4_core

    token = os.environ.get("GITHUB_TOKEN")
    g = load_redux4_core({"github_token": token})

    anchor_dirs = collect_anchors(archive, args.pilot_only)
    all_rows: List[Dict[str, object]] = []
    urls: List[str] = []

    for adir in anchor_dirs:
        for row in read_matches(adir / "30_Matches.csv", args.top_k):
            urls.extend([row["AnchorUrl"], row["CandidateUrl"]])

    urls = sorted({u for u in urls if u.startswith("https://github.com/")})

    if args.fit_global and g.get("GLOBAL_NORMALIZER") is None and urls:
        g["fit_global_normalizer"](
            urls,
            metrics=g.get("CAIS_METRICS"),
            token=token or g.get("github_token"),
            max_commits=args.max_commits,
            strategy="minmax",
        )

    for adir in anchor_dirs:
        anchor_rows = read_matches(adir / "30_Matches.csv", args.top_k)
        if not anchor_rows:
            continue
        anchor_name = anchor_rows[0]["AnchorRepo"]
        out_csv = anchor_out_csv(out_dir, anchor_name)
        if args.skip_existing and csv_has_scores(out_csv, args.top_k):
            print(f"  skip existing {out_csv.name}")
            continue

        per_anchor: List[Dict[str, object]] = []
        for row in anchor_rows:
            q = row["AnchorUrl"]
            t = row["CandidateUrl"]
            if not str(q).startswith("https://github.com/") or not str(t).startswith("https://github.com/"):
                continue
            try:
                scores = score_pair(
                    q, t, g, args.max_commits, metadata_only=args.metadata_only
                )
            except Exception as exc:  # noqa: BLE001
                scores = {"metadata_pct": "", "error": str(exc)[:300]}
                if not args.metadata_only:
                    scores.update(
                        {
                            "code_centric_pct": "",
                            "dynamic_pct": "",
                            "cross_language_pct": "",
                        }
                    )
            record = {
                "anchor_repo": row["AnchorRepo"],
                "anchor_url": q,
                "candidate_repo": row["CandidateRepo"],
                "candidate_url": t,
                "rank": row.get("Rank", ""),
                "metamatch_score": row.get("Score", ""),
                **scores,
            }
            per_anchor.append(record)
            all_rows.append(record)

        if per_anchor:
            with out_csv.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(per_anchor[0].keys()))
                writer.writeheader()
                writer.writerows(per_anchor)
            print(f"  wrote {out_csv}")

    n_rollup = write_rollup_from_dir(out_dir, args.top_k)
    if n_rollup:
        print(f"  rollup: {n_rollup} anchors -> {out_dir / 'rollup_summary.csv'}")

    by_anchor: Dict[str, List[Dict[str, object]]] = {}
    for r in all_rows:
        by_anchor.setdefault(str(r["anchor_repo"]), []).append(r)

    manifest = {
        "archive": str(archive),
        "pilot_only": args.pilot_only,
        "top_k": args.top_k,
        "max_commits": args.max_commits,
        "metadata_only": args.metadata_only,
        "skip_existing": args.skip_existing,
        "n_pair_scores": len(all_rows),
        "anchors_scored_this_run": sorted(by_anchor.keys()) if all_rows else [],
        "rollup_anchors": n_rollup,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_rows)} pair scores to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
