#!/usr/bin/env python3
"""Archive runs/_summaries and runs/manual-ml-py into runs/experiments/<experiment_id>/."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment_id", help="Folder name, e.g. penalty55_min700_cap21")
    ap.add_argument("--description", default="")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    exp_dir = root / "runs" / "experiments" / args.experiment_id
    summaries = root / "runs" / "_summaries"
    manual = root / "runs" / "manual-ml-py"

    if not summaries.is_dir():
        raise SystemExit(f"Missing {summaries}")
    if not manual.is_dir():
        raise SystemExit(f"Missing {manual}")

    if exp_dir.exists():
        shutil.rmtree(exp_dir)
    exp_dir.mkdir(parents=True)

    for item in summaries.iterdir():
        dest = exp_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    shutil.copytree(manual, exp_dir / "manual-ml-py")

    meta = {
        "experiment_id": args.experiment_id,
        "description": args.description or args.experiment_id,
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "source_summaries": str(summaries),
        "source_manual_ml_py": str(manual),
    }
    (exp_dir / "experiment_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(f"Archived to {exp_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
