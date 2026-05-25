#!/usr/bin/env python3
"""
Run MetaMatch grid search: penalty x minScore x owner caps.
Skips archives that already exist with matching hyperparameters.

Usage:
  python3 tools/run_metamatch_grid.py --dry-run
  python3 tools/run_metamatch_grid.py
  python3 tools/run_metamatch_grid.py --only penalty150_min700_cap21
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = ROOT / "runs" / "experiments"
PIPELINE = ROOT / "Run-MetaMatchPipeline.ps1"
PROGRESS = EXP_ROOT / "grid_phase2_progress.jsonl"
STOP_FILE = EXP_ROOT / "GRID_STOP_AFTER_CURRENT"

PENALTIES = [110, 125, 150, 175, 200]
MIN_SCORES = [700, 750, 800]
CAPS = [(1, 1), (1, 2), (2, 1), (2, 2)]
COMPARE_WITH = "penalty100_min700_cap21,penalty55_min700_cap21,penalty30_min700_cap21"
CHAMPION = "penalty100_min700_cap21"


def experiment_id(penalty: int, min_score: int, owner: int, sub: int) -> str:
    return f"penalty{penalty}_min{min_score}_cap{owner}{sub}"


def iter_grid():
    for penalty in PENALTIES:
        for min_score in MIN_SCORES:
            for owner, sub in CAPS:
                yield penalty, min_score, owner, sub, experiment_id(penalty, min_score, owner, sub)


def archive_hyperparams_match(exp_dir: Path, penalty: float, min_score: int, owner: int, sub: int) -> bool:
    hp = exp_dir / "run_hyperparams.csv"
    if not hp.exists():
        return False
    with hp.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return False
    r = rows[0]
    try:
        return (
            float(r.get("CrossAnchorFreqPenaltyWeight") or -1) == float(penalty)
            and int(float(r.get("MinimumScore") or -1)) == int(min_score)
            and int(float(r.get("MaxPerOwner") or -1)) == int(owner)
            and int(float(r.get("MaxPerOwnerPerSubdomain") or -1)) == int(sub)
        )
    except (TypeError, ValueError):
        return False


def should_skip(eid: str, penalty: int, min_score: int, owner: int, sub: int) -> bool:
    exp_dir = EXP_ROOT / eid
    eval_csv = exp_dir / "anchor_evaluation.csv"
    if not eval_csv.exists():
        return False
    return archive_hyperparams_match(exp_dir, penalty, min_score, owner, sub)


def run_one(
    penalty: int,
    min_score: int,
    owner: int,
    sub: int,
    eid: str,
    dry_run: bool,
) -> int:
    if should_skip(eid, penalty, min_score, owner, sub):
        print(f"[skip] {eid} (archive OK)")
        return 0

    cmd = [
        "pwsh",
        "-NoProfile",
        "-File",
        str(PIPELINE),
        f"-CrossAnchorFreqPenaltyWeight:{penalty}",
        f"-MinimumScore:{min_score}",
        f"-MaxPerOwner:{owner}",
        f"-MaxPerOwnerPerSubdomain:{sub}",
        f"-ArchiveAsExperiment:{eid}",
        f"-CompareWith:{COMPARE_WITH}",
    ]
    print(f"\n=== {eid} penalty={penalty} min={min_score} cap={owner}/{sub} ===")
    if dry_run:
        print(" ".join(cmd))
        return 0

    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(cmd, cwd=ROOT)
    line = {
        "experiment_id": eid,
        "penalty": penalty,
        "min_score": min_score,
        "max_owner": owner,
        "max_sub": sub,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "exit_code": proc.returncode,
    }
    with PROGRESS.open("a", encoding="utf-8") as f:
        import json

        f.write(json.dumps(line) + "\n")
    return proc.returncode


def stop_requested() -> bool:
    return STOP_FILE.exists()


def clear_stop_flag() -> None:
    if STOP_FILE.exists():
        STOP_FILE.unlink()


def list_all_experiment_ids() -> list[str]:
    """All archived experiments with anchor_evaluation.csv (grid + targeted runs)."""
    ids = set()
    if EXP_ROOT.is_dir():
        for p in EXP_ROOT.iterdir():
            if p.is_dir() and p.name.startswith("penalty") and (p / "anchor_evaluation.csv").exists():
                ids.add(p.name)
    return sorted(ids)


def finalize() -> int:
    ids = [eid for eid in list_all_experiment_ids() if (EXP_ROOT / eid).is_dir()]
    if not ids:
        print("No experiment archives found.")
        return 1
    cmd = ["python3", "tools/compare_experiments.py", "--experiments", *ids]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=False)
    for tool in ("pick_experiment_winner.py", "update_experiment_log.py"):
        subprocess.run(["python3", f"tools/{tool}"], cwd=ROOT, check=False)
    # apply only if pick script says beats champion — handled inside apply script
    subprocess.run(["python3", "tools/apply_experiment_winner.py"], cwd=ROOT, check=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", help="Run a single experiment_id")
    parser.add_argument("--finalize-only", action="store_true", help="Compare + WINNER.md only")
    parser.add_argument(
        "--stop-after-current",
        action="store_true",
        help="Create GRID_STOP_AFTER_CURRENT; exit after the in-flight experiment finishes",
    )
    args = parser.parse_args()

    if args.stop_after_current and not args.dry_run:
        STOP_FILE.write_text(
            f"stop requested {datetime.now(timezone.utc).isoformat()}\n",
            encoding="utf-8",
        )
        print(f"Wrote {STOP_FILE} — grid will stop after current experiment completes.")
        return 0

    if args.finalize_only:
        return finalize()

    clear_stop_flag()
    total = len(PENALTIES) * len(MIN_SCORES) * len(CAPS)
    print(f"Grid: {total} combinations ({len(PENALTIES)} penalties x {len(MIN_SCORES)} min x {len(CAPS)} caps)")
    print(f"Champion to beat: {CHAMPION}")

    failures = 0
    for penalty, min_score, owner, sub, eid in iter_grid():
        if args.only and eid != args.only:
            continue
        if stop_requested():
            print(f"Stop flag set ({STOP_FILE}); exiting before {eid}.")
            break
        rc = run_one(penalty, min_score, owner, sub, eid, args.dry_run)
        if rc != 0:
            failures += 1
            print(f"[warn] {eid} exited {rc}", file=sys.stderr)
        if stop_requested():
            print("Stop flag set; exiting after completed experiment.")
            break

    if not args.dry_run:
        finalize()
        clear_stop_flag()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
