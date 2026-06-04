#!/usr/bin/env python3
"""Write a lightweight run manifest for benchmark reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def sha256_for_file(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def gh_auth_state() -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=60,
        )
        return {
            "gh_available": True,
            "gh_authenticated": proc.returncode == 0,
            "gh_status_excerpt": proc.stdout[:1000],
        }
    except FileNotFoundError:
        return {
            "gh_available": False,
            "gh_authenticated": False,
            "gh_status_excerpt": "gh command not found",
        }



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results_benchmark/run_manifest.json")
    parser.add_argument("--benchmark", default="configs/labeled_benchmark_pairs.json")
    parser.add_argument("--hyperparams", default="metamatch_hyperparams.json")
    args = parser.parse_args()

    auth = gh_auth_state()
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(Path.cwd()),
        "github_token_present": bool(os.environ.get("GITHUB_TOKEN")),
        **auth,
        "benchmark_manifest_path": args.benchmark,
        "benchmark_manifest_sha256": sha256_for_file(Path(args.benchmark)),
        "hyperparams_path": args.hyperparams,
        "hyperparams_sha256": sha256_for_file(Path(args.hyperparams)),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote run manifest to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
