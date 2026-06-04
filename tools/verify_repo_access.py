#!/usr/bin/env python3
"""Verify benchmark repositories are reachable and git-log friendly.

This script is intentionally conservative: it checks whether each repository URL
can answer ``git ls-remote`` and, if enabled, whether a shallow clone can be
performed and ``git log`` returns commit history.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def run_cmd(cmd: List[str], cwd: Path | None = None, timeout: int = 120) -> Tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()



def load_pairs(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict):
        return list(payload.get("pairs", []))
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported benchmark manifest structure in {path}")



def verify_repo(url: str, pin: str | None, perform_clone: bool) -> Dict[str, object]:
    result: Dict[str, object] = {
        "repo_url": url,
        "pin": pin or "",
        "ls_remote_ok": False,
        "clone_ok": False,
        "git_log_ok": False,
        "pin_found": False,
        "details": "",
    }
    code, out = run_cmd(["git", "ls-remote", url], timeout=120)
    result["ls_remote_ok"] = code == 0
    result["details"] = out[:500]
    if code != 0:
        return result

    if pin:
        pin_code, pin_out = run_cmd(["git", "ls-remote", url, pin], timeout=120)
        result["pin_found"] = pin_code == 0 and bool(pin_out.strip())

    if not perform_clone:
        return result

    with tempfile.TemporaryDirectory(prefix="repo_access_") as tmpdir:
        target = Path(tmpdir) / "repo"
        clone_cmd = ["git", "clone", "--depth", "20", url, str(target)]
        code, out = run_cmd(clone_cmd, timeout=300)
        result["clone_ok"] = code == 0
        result["details"] = out[:500]
        if code != 0:
            return result

        log_code, log_out = run_cmd(["git", "log", "--oneline", "-n", "5"], cwd=target, timeout=120)
        result["git_log_ok"] = log_code == 0 and bool(log_out.strip())
        if log_out.strip():
            result["details"] = log_out.splitlines()[0][:500]
    return result



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="configs/labeled_benchmark_pairs.json")
    parser.add_argument("--output", default="results_benchmark/repo_access_validation.csv")
    parser.add_argument("--skip-clone", action="store_true")
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    pairs = load_pairs(benchmark_path)
    rows: List[Dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    for pair in pairs:
        for side in ("a", "b"):
            url = str(pair.get(f"repo_{side}_url", "")).strip()
            if not url:
                continue
            pin = str(pair.get(f"pin_{side}", "")).strip() or None
            key = (url, pin or "")
            if key in seen:
                continue
            seen.add(key)
            verified = verify_repo(url, pin, perform_clone=not args.skip_clone)
            verified["pair_ids"] = ",".join(
                sorted(
                    str(p.get("pair_id"))
                    for p in pairs
                    if str(p.get(f"repo_{side}_url", "")).strip() == url
                )
            )
            rows.append(verified)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "repo_url",
        "pin",
        "ls_remote_ok",
        "clone_ok",
        "git_log_ok",
        "pin_found",
        "pair_ids",
        "details",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} repo-access validation rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
