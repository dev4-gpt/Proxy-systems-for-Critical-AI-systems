"""Auto-extracted from proxytool_REDUX_4.ipynb — re-run scripts/extract_redux4_core.py."""
from __future__ import annotations

# Overrides for extracted REPRO runs (full notebook keeps its own flags).
RUN_SLOW_TESTS = False


# --- notebook cell 8 (id=ed377224) ---
# test
import requests, tqdm, sentence_transformers, vaderSentiment, matplotlib, scipy, numpy, pandas, sklearn, psutil
print("All imports successful!")

# --- notebook cell 9 (id=a8a2c432) ---
# Control flags to skip long-running/archival cells
RUN_SLOW_TESTS = True  # set to True to run slow/archival suites
SKIP_MSG = "Skipped slow cell: set RUN_SLOW_TESTS=True to run"

# --- notebook cell 10 (id=b2afba1a) ---

import argparse
import json
import math
import re
import statistics as stats
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import requests
from tqdm import tqdm  # pip install --upgrade tqdm

# Logging switches (set by CLI)
VERBOSE = False
QUIET = False


def _log(msg: str, level: str = "info"):
    """Minimal logger with quiet/verbose control."""
    if level == "debug" and not VERBOSE:
        return
    if QUIET and level in ("info", "debug"):
        return
    print(msg)

# --- notebook cell 11 (id=59078310) ---
# Ensure sentence-transformers is available (for deep_code_similarity and commit embeddings)
try:
    import sentence_transformers  # noqa: F401
    _st_ready = True
except ImportError:
    _st_ready = False
if not _st_ready:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"])
    import sentence_transformers  # noqa: F401
    _st_ready = True
if _st_ready:
    print("sentence-transformers ready (deep_code_similarity and commit embeddings will use it).")

# --- notebook cell 12 (id=57adb925) ---
import os
from pathlib import Path

# Single place for GitHub token (used everywhere else in the notebook).
# Reads from (in order): environment variable, .env file, or token.txt.
# NEVER hardcode a token in this notebook.
github_token = os.environ.get("GITHUB_TOKEN")

if not github_token:
    _env_file = Path(".env")
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("GITHUB_TOKEN=") and not line.startswith("#"):
                github_token = line.split("=", 1)[1].strip()
                break

if not github_token:
    _token_file = Path("token.txt")
    if _token_file.exists():
        github_token = _token_file.read_text().strip()

if not github_token or github_token.startswith("<REDACTED"):
    raise RuntimeError(
        "GitHub token not found. Provide it in ONE of these ways:\n"
        "  1. Put GITHUB_TOKEN=ghp_... in a .env file in this folder.\n"
        "  2. Create a token.txt file with just the token.\n"
        "  3. Or set the GITHUB_TOKEN env var before starting Jupyter."
    )

print(f"GitHub token loaded ({github_token[:4]}...{github_token[-4:]})")

# --- notebook cell 14 (id=fb9bc515) ---
def check_github_token(token: str | None = None) -> bool:
    """Quick health-check: hit /rate_limit and report whether the token is accepted."""
    token = token or github_token
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "proxytool/0.1"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        r = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=10)
        if r.status_code == 401:
            print(f"Token REJECTED (401). Generate a new PAT and update .env.")
            return False
        data = r.json().get("rate", {})
        print(
            f"Token OK — core API: {data.get('remaining', '?')}/{data.get('limit', '?')} "
            f"requests remaining (resets {data.get('reset', '?')})"
        )
        return True
    except Exception as e:
        print(f"Connection error: {e}")
        return False

check_github_token()

# --- notebook cell 16 (id=d362d485) ---
CACHE_DIR = Path(".proxytool_cache")
CACHE_DIR.mkdir(exist_ok=True)


def cache_key(owner: str, repo: str, since: Optional[str], until: Optional[str]) -> str:
    return f"{owner}_{repo}_{since or 'none'}_{until or 'none'}.json"


def load_cached_commits(owner: str, repo: str, since: Optional[str], until: Optional[str]) -> Optional[List[dict]]:
    path = CACHE_DIR / cache_key(owner, repo, since, until)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _log(f"  [Cache hit] Loaded {len(data)} commits", "debug")
                return data
        except Exception as e:
            _log(f"  [Cache error] {e}", "debug")
    return None


def save_cached_commits(owner: str, repo: str, since: Optional[str], until: Optional[str], commits: List[dict]):
    path = CACHE_DIR / cache_key(owner, repo, since, until)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(commits, f, indent=None)
        _log(f"  [Cache saved] {len(commits)} commits", "debug")
    except Exception as e:
        _log(f"  [Cache save failed] {e}", "debug")

# --- notebook cell 18 (id=b3236e58) ---
@dataclass
class CommitRecord:
    repo_id: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int
    touched_files: List[str] = field(default_factory=list)

    @property
    def lines_changed(self) -> int:
        return (self.insertions or 0) + (self.deletions or 0)

# --- notebook cell 19 (id=9ce83b76) ---
# Core metric sets used across the notebook
# BASE_METRICS: original 5 families
BASE_METRICS = "sentiment,churn,attach,cadence,gitlogger"

# CAIS_METRICS: full metric set used for CAIS-aware similarity
CAIS_METRICS = (
    "sentiment,churn,attach,cadence,gitlogger,"  # base
    "environment,purpose,operational,algorithm,language,"  # NIST 5D taxonomy dimensions
    "commitsem,contributors,cochange,temporal,embedding,"  # paper-driven metadata fingerprints
    "release_cadence,branching,issue_metrics,doc_quality,ci_signals"  # proxy / maturity signals
)

# --- notebook cell 21 (id=409c13a3) ---
def run_git_log(
    repo: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    max_commits: Optional[int] = None,
) -> List[CommitRecord]:
    repo_path = Path(repo)
    if not repo_path.exists():
        raise FileNotFoundError(f"Local repo not found: {repo}")

    fmt = "@@@%H\x1f%an\x1f%ae\x1f%ad\x1f%s"
    args = [
        "git", "-C", str(repo_path), "log", "--no-merges",
        f"--pretty=format:{fmt}", "--date=iso-strict", "--numstat"
    ]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if max_commits:
        args.append(f"-n{int(max_commits)}")

    try:
        out = subprocess.check_output(args, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git log failed: {e.output}")

    recs: List[CommitRecord] = []
    current: Optional[Dict] = None

    def flush():
        nonlocal current, recs
        if not current:
            return
        dt = datetime.fromisoformat(current["date"])
        recs.append(CommitRecord(
            repo_id=str(repo_path.resolve()),
            author=current.get("author", "unknown"),
            email=current.get("email", "unknown"),
            date=dt,
            message=current.get("message", ""),
            files_changed=int(current.get("files_changed", 0)),
            insertions=int(current.get("insertions", 0)),
            deletions=int(current.get("deletions", 0)),
            touched_files=current.get("touched_files", []),
        ))
        current = None

    for line in out.splitlines():
        if line.startswith("@@@"):
            flush()
            parts = line[3:].split("\x1f")
            if len(parts) < 5:
                continue
            current = {
                "files_changed": 0, "insertions": 0, "deletions": 0,
                "author": parts[1].strip(), "email": parts[2].strip(),
                "date": parts[3].strip(), "message": parts[4].strip(),
                "touched_files": [],
            }
        elif line.strip() and current is not None:
            ins, dels, path = line.split("\t")[:3]
            current["files_changed"] += 1
            current["insertions"] += int(ins) if ins.isdigit() else 0  # '-' for binaries
            current["deletions"] += int(dels) if dels.isdigit() else 0
            current["touched_files"].append(path)
    flush()
    return recs

# --- notebook cell 23 (id=a1155076) ---
GITHUB_API = "https://api.github.com"
MAX_RETRIES_5XX = 4
BASE_DELAY_5XX = 2.0


def _github_request_with_progress(
    url: str,
    token: Optional[str],
    params: Optional[dict],
    paginate: bool,
    pbar: Optional[tqdm] = None,
) -> Iterator[dict]:
    """Robust request with rate limit + progress (pbar may be None)."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "proxytool/0.1 (+metadata-only-similarity)",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    while url:
        resp = None
        for attempt in range(MAX_RETRIES_5XX):
            try:
                resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
                resp.raise_for_status()
                break
            except requests.exceptions.Timeout:
                raise RuntimeError("Request timeout after 30s")
            except requests.HTTPError as e:
                r = getattr(e, "response", None) or resp
                if r is not None and 500 <= r.status_code < 600:
                    if attempt < MAX_RETRIES_5XX - 1:
                        delay = BASE_DELAY_5XX * (2 ** attempt)
                        _log(f"  GitHub {r.status_code}, retrying in {delay:.0f}s (attempt {attempt+1}/{MAX_RETRIES_5XX})...", "info")
                        time.sleep(delay)
                        continue
                if r is not None and r.status_code == 403:
                    msg = ""
                    if "application/json" in r.headers.get("Content-Type", ""):
                        try:
                            msg = r.json().get("message", "")
                        except Exception:
                            msg = ""
                    if "rate limit" in (msg or "").lower():
                        reset = int(r.headers.get("X-RateLimit-Reset", 0))
                        sleep = max(reset - time.time(), 0) + 5
                        reset_time = datetime.fromtimestamp(reset).strftime("%H:%M:%S")
                        _log(f"  Rate limit exceeded. Sleeping {sleep:.0f}s until {reset_time}...", "info")
                        time.sleep(sleep)
                        continue
                    raise RuntimeError(f"GitHub 403: {msg}")
                raise

        remaining = int(resp.headers.get("X-RateLimit-Remaining", 0) or 0)
        limit = int(resp.headers.get("X-RateLimit-Limit", 5000) or 5000)
        if remaining < 100:
            _log(f"  Rate limit: {remaining}/{limit} remaining", "debug")

        data = resp.json()
        if isinstance(data, list):
            for item in data:
                yield item
                if pbar is not None:
                    pbar.update(1)
        else:
            yield data
            if pbar is not None:
                pbar.update(1)

        if not paginate:
            break

        link = resp.headers.get("Link", "")
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1: part.find(">")]
                break
        time.sleep(0.2)

# --- notebook cell 24 (id=477846f1) ---
def run_github_log(
    owner: str,
    repo: str,
    token: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    max_commits: Optional[int] = None,
) -> List[CommitRecord]:
    repo_slug = f"{owner}/{repo}"
    commits_url = f"{GITHUB_API}/repos/{repo_slug}/commits"
    params = {"per_page": 100}
    if since:
        params["since"] = f"{since}T00:00:00Z"
    if until:
        params["until"] = f"{until}T23:59:59Z"

    cached = load_cached_commits(owner, repo, since, until)
    if cached:
        return [
            CommitRecord(
                repo_id=f"github:{repo_slug}",
                author=c["author"], email=c["email"],
                date=datetime.fromisoformat(c["date"].replace("Z", "+00:00")),
                message=c["message"], files_changed=c["files_changed"],
                insertions=c["insertions"], deletions=c["deletions"],
                touched_files=c.get("touched_files", []),
            ) for c in cached
        ]

    records: List[CommitRecord] = []
    seen = 0
    last_progress = time.time()

    _log(f"  Fetching commits from {repo_slug}...", "info")
    with tqdm(desc="Commits", unit="c", position=0, leave=not QUIET, disable=QUIET) as pbar:
        for commit in _github_request_with_progress(commits_url, token, params, paginate=True, pbar=pbar):
            if max_commits and seen >= max_commits:
                break
            if time.time() - last_progress > 300:
                raise RuntimeError("No progress in 5 minutes — aborting")

            sha = commit["sha"]
            author = commit["commit"]["author"]["name"]
            email = commit["commit"]["author"]["email"]
            date_str = commit["commit"]["author"]["date"]
            message = commit["commit"]["message"].split("\n", 1)[0]

            details_url = f"{GITHUB_API}/repos/{repo_slug}/commits/{sha}"
            details = next(_github_request_with_progress(details_url, token, {}, paginate=False, pbar=None))

            stats_d = details.get("stats", {}) or {}
            files = details.get("files", []) or []
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            insertions = stats_d.get("additions") or 0
            deletions = stats_d.get("deletions") or 0

            records.append(CommitRecord(
                repo_id=f"github:{repo_slug}",
                author=author, email=email, date=dt, message=message,
                files_changed=len(files),
                insertions=insertions,
                deletions=deletions,
                touched_files=[f.get("filename", "") for f in files if f.get("filename")],
            ))
            seen += 1
            last_progress = time.time()
            if pbar is not None:
                pbar.set_postfix({"fetched": seen})

    cache_data = [{
        "author": r.author, "email": r.email, "date": r.date.isoformat(),
        "message": r.message, "files_changed": r.files_changed,
        "insertions": r.insertions, "deletions": r.deletions,
        "touched_files": r.touched_files,
    } for r in records]
    save_cached_commits(owner, repo, since, until, cache_data)

    return records

# --- notebook cell 26 (id=2408c231) ---
class SentimentBackend:
    def score(self, text: str) -> Dict[str, float]:
        raise NotImplementedError


class VaderBackend(SentimentBackend):
    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self._an = SentimentIntensityAnalyzer()

    def score(self, text: str) -> Dict[str, float]:
        s = self._an.polarity_scores(text or "")
        return {"pos": s["pos"], "neu": s["neu"], "neg": s["neg"], "compound": s["compound"]}


class TinyLexiconBackend(SentimentBackend):
    POS = set("good great awesome excellent nice improved success happy fix stable".split())
    NEG = set("bad worse terrible broken fail bug slow flaky regress revert urgent".split())

    def score(self, text: str) -> Dict[str, float]:
        words = re.findall(r"[a-zA-Z]+", (text or "").lower())
        pos = sum(w in self.POS for w in words)
        neg = sum(w in self.NEG for w in words)
        total = max(pos + neg, 1)
        compound = (pos - neg) / total
        p = n = 0.1; neu = 0.8
        if pos > neg:
            p, n = 0.6, 0.1
        elif neg > pos:
            p, n = 0.1, 0.6
        else:
            p = n = 0.2; neu = 0.6
        return {"pos": p, "neu": neu, "neg": n, "compound": compound}


def get_sentiment_backend() -> SentimentBackend:
    try:
        return VaderBackend()
    except Exception:
        return TinyLexiconBackend()


_issue_regex = re.compile(
    r"(?i)(?:\b(?:fix(?:es|ed)?|close(?:s|d)?|resolve(?:s|d)?)\s*)?(?:#|gh-)?(\d{1,7})\b"
    r"|\bissue\s*(\d{1,7})\b|\bPR\s*#(\d{1,7})\b"
)

# --- notebook cell 27 (id=fc8bedf8) ---
class Metric:
    name: str = "base"
    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        raise NotImplementedError


def _entropy(p: List[float]) -> float:
    return -sum(pi * math.log(pi + 1e-12) for pi in p if pi > 0)


class CadenceMetric(Metric):
    name = "cadence"
    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {"commit_count": 0.0, "commit_cadence_per_day": 0.0}
        cs = sorted(commits, key=lambda c: c.date)
        days = max((cs[-1].date - cs[0].date).days, 0) + 1
        cadence = len(cs) / days if days > 0 else 0.0
        return {
            "commit_count": float(len(cs)),
            "commit_cadence_per_day": cadence
        }


class ChurnMetric(Metric):
    name = "churn"
    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {
                "churn_avg_files": 0.0,
                "lines_changed_total": 0.0,
                "net_lines_changed": 0.0
            }
        files_per = [c.files_changed for c in commits]
        return {
            "churn_avg_files": stats.fmean(files_per),
            "lines_changed_total": float(sum(c.lines_changed for c in commits)),
            "net_lines_changed": float(sum(c.insertions - c.deletions for c in commits))
        }

# --- notebook cell 28 (id=c0e64a82) ---
class SentimentMetric(Metric):
    name = "sentiment"
    def __init__(self):
        self.backend = get_sentiment_backend()

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {f"sent_{k}": 0.0 for k in "mean std pos_share neu_share neg_share entropy weekly_volatility by_author_gini".split()}
        scores = [self.backend.score(c.message) for c in commits]
        comp = [s["compound"] for s in scores]
        mean = stats.fmean(comp)
        std = stats.pstdev(comp) if len(comp) > 1 else 0.0

        # Winner-take-most class shares
        winners = [max(("pos", s["pos"]), ("neu", s["neu"]), ("neg", s["neg"]), key=lambda x: x[1])[0] for s in scores]
        pos = sum(1 for w in winners if w == "pos") / len(winners)
        neu = sum(1 for w in winners if w == "neu") / len(winners)
        neg = 1.0 - pos - neu
        entropy = _entropy([pos, neu, neg])

        # Weekly volatility of mean compound
        weekly: Dict[Tuple[int, int], List[float]] = {}
        for c, s in zip(commits, scores):
            week = c.date.isocalendar()[:2]  # (year, week)
            weekly.setdefault(week, []).append(s["compound"])
        weekly_vol = stats.pstdev([stats.fmean(v) for v in weekly.values()]) if len(weekly) > 1 else 0.0

        # Inequality of sentiment by author (Gini on |mean|)
        by_author: Dict[str, List[float]] = {}
        for c, s in zip(commits, scores):
            by_author.setdefault(c.author, []).append(s["compound"])
        author_means = [abs(stats.fmean(v)) for v in by_author.values()]
        gini = 0.0
        if author_means:
            n = len(author_means)
            total = sum(author_means)
            cum = sum((i + 1) * x for i, x in enumerate(sorted(author_means)))
            gini = (2 * cum) / (n * total) - (n + 1) / n if total > 0 else 0.0

        return {
            "sent_mean": mean, "sent_std": std, "sent_pos_share": pos, "sent_neu_share": neu,
            "sent_neg_share": neg, "sent_entropy": entropy, "sent_weekly_volatility": weekly_vol,
            "sent_by_author_gini": gini
        }


class AttachRateMetric(Metric):
    name = "attach"
    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {"attach_rate": 0.0, "issue_breadth": 0.0}
        with_issue = 0
        issues = set()
        for c in commits:
            ids = {g for m in _issue_regex.finditer(c.message or "") for g in m.groups() if g}
            if ids:
                with_issue += 1
                issues.update(ids)
        return {"attach_rate": with_issue / len(commits), "issue_breadth": float(len(issues))}

# --- notebook cell 29 (id=cd509d6e) ---
class GitLoggerMetrics(Metric):
    """
    GitLogger-standardized metrics for comparison testing.
    Reference: https://gitlogger.com/GitLogger-Metrics/

    These metrics use the exact naming conventions from GitLogger for:
    1. LineCadence - total lines changed / time between commits
    2. NetLineCadence - net lines (insertions-deletions) / time between commits
    3. CommitRepeats - count of repeated commit messages
    4. BusyDayOfWeek - lines changed grouped by day of week (returns entropy)
    """
    name = "gitlogger"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {
                "gl_line_cadence": 0.0,
                "gl_net_line_cadence": 0.0,
                "gl_commit_repeats": 0.0,
                "gl_busy_day_entropy": 0.0
            }

        cs = sorted(commits, key=lambda c: c.date)
        total_lines = sum(c.lines_changed for c in cs)
        days_active = max((cs[-1].date - cs[0].date).days, 0) + 1
        line_cadence = total_lines / days_active if days_active > 0 else 0.0

        net_lines = sum(c.insertions - c.deletions for c in cs)
        net_line_cadence = net_lines / days_active if days_active > 0 else 0.0

        messages = [c.message.strip().lower() for c in cs]
        repeats = len(messages) - len(set(messages))

        day_lines = {i: 0 for i in range(7)}
        for c in cs:
            day_lines[c.date.weekday()] += c.lines_changed

        total = sum(day_lines.values()) or 1
        probs = [v / total for v in day_lines.values()]
        busy_day_entropy = _entropy(probs)

        return {
            "gl_line_cadence": line_cadence,
            "gl_net_line_cadence": net_line_cadence,
            "gl_commit_repeats": float(repeats),
            "gl_busy_day_entropy": busy_day_entropy
        }


def _keyword_frequency(corpus: str, keywords: Dict[str, List[str]], prefix: str) -> Dict[str, float]:
    words = re.findall(r"[a-z_]+", corpus.lower())
    total = max(len(words), 1)
    return {
        f"{prefix}{k}": sum(words.count(w.lower()) for w in vals) / total
        for k, vals in keywords.items()
    }


class EnvironmentMetric(Metric):
    name = "environment"
    KEYWORDS = {
        "land": ["gps", "terrain", "ground", "vehicle", "navigation", "obstacle", "lidar"],
        "air": ["uav", "drone", "altitude", "airspace", "flight", "aerial"],
        "sea": ["maritime", "ocean", "underwater", "buoy", "vessel", "sonar"],
        "space": ["satellite", "orbit", "spacecraft", "launch", "telemetry"],
        "cyber": ["cloud", "api", "network", "server", "database", "endpoint", "docker"],
        "medical": ["patient", "clinical", "diagnosis", "ehr", "sensor", "vital", "triage"],
    }

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        corpus = " ".join(c.message for c in commits)
        return _keyword_frequency(corpus, self.KEYWORDS, "env_")


class PurposeMetric(Metric):
    name = "purpose"
    DOMAINS = {
        "reasoning": ["reasoning", "inference", "logic", "expert", "knowledge"],
        "planning": ["planning", "scheduler", "optimization", "constraint", "search"],
        "learning": ["train", "model", "dataset", "epoch", "loss", "gradient", "accuracy"],
        "communication": ["chat", "dialog", "conversation", "assistant", "messaging"],
        "perception": ["vision", "image", "detect", "classify", "segment", "camera", "lidar"],
        "integration": ["workflow", "pipeline", "integration", "orchestration", "interface"],
        "robotics": ["robot", "actuator", "servo", "kinematics", "ros", "motion"],
        "vehicles": ["vehicle", "autopilot", "steering", "lane", "collision", "adas"],
        "services": ["api", "dashboard", "analytics", "report", "alert", "service"],
    }

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        corpus = " ".join(c.message for c in commits)
        return _keyword_frequency(corpus, self.DOMAINS, "purpose_")


class OperationalMetric(Metric):
    name = "operational"
    RISK_HINTS = {
        "risk_financial": ["cost", "fraud", "financial", "loss", "penalty", "liability"],
        "risk_social": ["public", "compliance", "privacy", "ethics", "fairness", "bias"],
        "risk_human": ["safety", "injury", "fatal", "harm", "patient", "critical"],
        "mission_autonomy": ["autonomous", "auto", "self-driving", "closed-loop", "real-time"],
        "failure_modes": ["failure", "fallback", "degraded", "incident", "outage", "fault"],
    }

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        corpus = " ".join(c.message for c in commits)
        return _keyword_frequency(corpus, self.RISK_HINTS, "op_")


class AlgorithmMetric(Metric):
    name = "algorithm"
    ALGOS = {
        "deep_learning": ["neural", "cnn", "lstm", "transformer", "bert", "attention", "backprop"],
        "tree_based": ["decision_tree", "random_forest", "xgboost", "catboost", "gradient_boost"],
        "regression": ["linear_regression", "logistic", "lasso", "ridge", "regression"],
        "clustering": ["kmeans", "hierarchical", "dbscan", "cluster"],
        "svm": ["svm", "support_vector", "kernel"],
        "reinforcement": ["reward", "policy", "q_learning", "agent", "environment", "rl"],
    }

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        corpus = " ".join(c.message for c in commits)
        return _keyword_frequency(corpus, self.ALGOS, "algo_")


class LanguageMetric(Metric):
    name = "language"
    EXT_LANGS = {
        ".py": "python", ".cpp": "cpp", ".cc": "cpp", ".c": "c", ".java": "java", ".js": "javascript",
        ".ts": "typescript", ".cs": "csharp", ".rb": "ruby", ".go": "go", ".rs": "rust", ".scala": "scala",
        ".swift": "swift", ".kt": "kotlin", ".jl": "julia", ".r": "r", ".php": "php", ".sh": "shell",
    }

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        counts: Dict[str, int] = {}
        for c in commits:
            for f in c.touched_files:
                ext = Path(f).suffix.lower()
                label = self.EXT_LANGS.get(ext)
                if label:
                    counts[label] = counts.get(label, 0) + 1

        total = max(sum(counts.values()), 1)
        return {f"lang_{k}": v / total for k, v in counts.items()}

# --- notebook cell 30 (id=46263bf0) ---
# Paper-driven metadata fingerprints (commit semantics, contributors, co-change, temporal, embedding)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{1,}")


def _tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text or "")]


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


class CommitSemanticMetric(Metric):
    """Lightweight semantic proxy for commit-message intent (domain/purpose overlap)."""

    name = "commitsem"

    LEXICONS = {
        "autonomy": {
            "autonomous", "autonomy", "adas", "lane", "lateral", "longitudinal", "brake", "steer", "trajectory",
            "perception", "planning", "localization", "sensor", "lidar", "radar", "camera", "fusion", "controller",
            "vehicle", "driving", "openpilot", "autoware", "apollo",
        },
        "medical": {
            "clinical", "patient", "triage", "diagnosis", "diagnostic", "sepsis", "icu", "ehr", "radiology",
            "imaging", "ct", "mri", "tumor", "segmentation", "inference", "risk", "alert", "workflow",
        },
        "robotics": {
            "robot", "robotics", "ros", "ros2", "navigation", "slam", "odometry", "control", "actuator",
            "planner", "trajectory", "localization", "mapping",
        },
        "aerial": {
            "drone", "uav", "flight", "autopilot", "px4", "ardupilot", "altitude", "gps", "imu", "mission",
            "waypoint", "failsafe",
        },
        "finance": {
            "fraud", "credit", "risk", "score", "scoring", "lending", "loan", "default", "aml", "kyc",
            "transaction", "payment", "underwriting",
        },
        "ml": {
            "model", "train", "training", "dataset", "loss", "optimizer", "inference", "feature", "label",
            "classification", "regression", "reinforcement", "neural", "transformer",
        },
        "safety": {
            "safety", "safe", "hazard", "fault", "failsafe", "mitigation", "incident", "adversarial", "robust",
            "attack", "security",
        },
    }

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {f"sem_{k}": 0.0 for k in self.LEXICONS}
        toks: List[str] = []
        for c in commits:
            toks.extend(_tokenize(c.message))
        total = float(len(toks))
        if total <= 0:
            return {f"sem_{k}": 0.0 for k in self.LEXICONS}
        counts: Dict[str, int] = {}
        for key, vocab in self.LEXICONS.items():
            counts[key] = sum(1 for t in toks if t in vocab)
        return {f"sem_{k}": _safe_div(v, total) for k, v in counts.items()}


class ContributorMetric(Metric):
    """Sociotechnical signature: author distribution, bus factor proxy, entropy."""

    name = "contributors"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {
                "contrib_author_count": 0.0,
                "contrib_top1_share": 0.0,
                "contrib_top2_share": 0.0,
                "contrib_bus_factor_50": 0.0,
                "contrib_entropy": 0.0,
            }
        by_author: Dict[str, int] = {}
        for c in commits:
            by_author[c.author] = by_author.get(c.author, 0) + 1
        total = float(sum(by_author.values()))
        shares = sorted((v / total for v in by_author.values()), reverse=True)
        top1 = shares[0] if shares else 0.0
        top2 = (shares[0] + shares[1]) if len(shares) > 1 else top1
        cum = 0.0
        bf = 0
        for s in shares:
            cum += s
            bf += 1
            if cum >= 0.5:
                break
        ent = _entropy(shares) if shares else 0.0
        return {
            "contrib_author_count": float(len(by_author)),
            "contrib_top1_share": float(top1),
            "contrib_top2_share": float(top2),
            "contrib_bus_factor_50": float(bf),
            "contrib_entropy": float(ent),
        }


class CochangeMetric(Metric):
    """Architecture-by-cochange proxy using touched_files per commit."""

    name = "cochange"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {
                "cochg_unique_files": 0.0,
                "cochg_avg_files_per_commit": 0.0,
                "cochg_edge_density": 0.0,
                "cochg_mean_degree": 0.0,
                "cochg_max_degree": 0.0,
            }
        file_counts: Dict[str, int] = {}
        edges: Dict[Tuple[str, str], int] = {}
        files_per_commit: List[int] = []
        for c in commits:
            files = [f for f in dict.fromkeys(c.touched_files) if f]
            files = files[:30]
            files_per_commit.append(len(files))
            for f in files:
                file_counts[f] = file_counts.get(f, 0) + 1
            for i in range(len(files)):
                for j in range(i + 1, len(files)):
                    a, b = files[i], files[j]
                    if a > b:
                        a, b = b, a
                    edges[(a, b)] = edges.get((a, b), 0) + 1
        unique_files = len(file_counts)
        avg_files = stats.fmean(files_per_commit) if files_per_commit else 0.0
        deg: Dict[str, int] = {f: 0 for f in file_counts}
        for (a, b) in edges.keys():
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        degrees = list(deg.values())
        mean_deg = stats.fmean(degrees) if degrees else 0.0
        max_deg = max(degrees) if degrees else 0.0
        possible = unique_files * (unique_files - 1) / 2
        density = _safe_div(float(len(edges)), float(possible)) if possible > 0 else 0.0
        return {
            "cochg_unique_files": float(unique_files),
            "cochg_avg_files_per_commit": float(avg_files),
            "cochg_edge_density": float(density),
            "cochg_mean_degree": float(mean_deg),
            "cochg_max_degree": float(max_deg),
        }


class TemporalRhythmMetric(Metric):
    """Development rhythm as a time-series fingerprint (weekly bins)."""

    name = "temporal"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        if not commits:
            return {
                "temp_weeks": 0.0,
                "temp_commits_per_week_mean": 0.0,
                "temp_commits_per_week_std": 0.0,
                "temp_burstiness": 0.0,
                "temp_idle_ratio": 0.0,
            }
        cs = sorted(commits, key=lambda c: c.date)
        weekly: Dict[Tuple[int, int], int] = {}
        for c in cs:
            wk = c.date.isocalendar()[:2]
            weekly[wk] = weekly.get(wk, 0) + 1
        weeks = sorted(weekly.keys())
        counts = [weekly[w] for w in weeks]
        mean = stats.fmean(counts) if counts else 0.0
        std = stats.pstdev(counts) if len(counts) > 1 else 0.0
        burst = _safe_div(std, mean) if mean > 0 else 0.0
        first, last = cs[0].date, cs[-1].date
        span_weeks = max(int((last - first).days / 7), 0) + 1
        observed_weeks = len(weekly)
        idle = max(span_weeks - observed_weeks, 0)
        idle_ratio = _safe_div(float(idle), float(span_weeks)) if span_weeks > 0 else 0.0
        return {
            "temp_weeks": float(span_weeks),
            "temp_commits_per_week_mean": float(mean),
            "temp_commits_per_week_std": float(std),
            "temp_burstiness": float(burst),
            "temp_idle_ratio": float(idle_ratio),
        }


COMMIT_EMBED_DIM = 32
_sentence_encoder = None


def _get_sentence_encoder():
    """Lazy-load sentence encoder. Returns model or False if unavailable."""
    global _sentence_encoder
    if _sentence_encoder is not None:
        return _sentence_encoder
    try:
        from sentence_transformers import SentenceTransformer
        _sentence_encoder = SentenceTransformer("all-MiniLM-L6-v2")
        return _sentence_encoder
    except Exception as e:
        _log(f"  [Embedding] sentence_transformers not available: {e}. Install with: pip install sentence-transformers", "info")
        _sentence_encoder = False
        return False


def _l2_norm(vec: List[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


class CommitEmbeddingMetric(Metric):
    """Embed commit messages in a semantic space (paper: NLP to embed messages)."""

    name = "embedding"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        out = {f"emb_{i}": 0.0 for i in range(COMMIT_EMBED_DIM)}
        if not commits:
            return out
        encoder = _get_sentence_encoder()
        if encoder is False:
            return out
        messages = [c.message.strip() or "(no message)" for c in commits]
        try:
            emb = encoder.encode(messages, show_progress_bar=False, convert_to_numpy=True)
        except Exception as e:
            _log(f"  [Embedding] encode failed: {e}", "debug")
            return out
        if emb.size == 0:
            return out
        mean_vec = emb.mean(axis=0).tolist()
        dim = min(COMMIT_EMBED_DIM, len(mean_vec))
        normalized = _l2_norm(mean_vec[:dim])
        for i in range(dim):
            out[f"emb_{i}"] = float(normalized[i])
        return out

# --- notebook cell 31 (id=4d397304) ---

import contextlib
import hashlib
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

import requests

# Repo context for metrics that need local git / filesystem (not just commit records).
_REPO_SIGNALS_CTX: Dict[str, object] = {}


class RepoSignalsContext(NamedTuple):
    repo: str
    github_token: Optional[str]
    git_path: str


def _repo_signals_context_active() -> Optional[RepoSignalsContext]:
    v = _REPO_SIGNALS_CTX.get("ctx")
    return v if isinstance(v, RepoSignalsContext) else None


@contextlib.contextmanager
def repo_signals_context(ctx: RepoSignalsContext):
    tok = _REPO_SIGNALS_CTX.get("ctx")
    _REPO_SIGNALS_CTX["ctx"] = ctx
    try:
        yield
    finally:
        if tok is None:
            _REPO_SIGNALS_CTX.pop("ctx", None)
        else:
            _REPO_SIGNALS_CTX["ctx"] = tok


_WORKTREE_CACHE: Dict[str, str] = {}


def _repo_signals_key(repo: str) -> str:
    s = repo.strip()
    if re.match(r"https?://github\.com/", s):
        return "gh:" + s.split("?", 1)[0].rstrip("/").lower()
    if "/" in s and not Path(s).exists():
        return "ghspec:" + s.strip().lower()
    return "url:" + hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _github_public_https_url(owner: str, name: str) -> str:
    """Clone URL without embedded credentials (avoids leaking PAT in errors/logs)."""
    return f"https://github.com/{owner}/{name}.git"


def _ensure_shallow_worktree(repo: str, token: Optional[str]) -> str:
    """Return a local checkout path suitable for scanning README/docs/CI files.

    Uses an unauthenticated https://github.com/... URL so failures never echo
    x-access-token:... in tracebacks or saved notebook outputs.

    For private repos, use host-level auth (e.g. `gh auth login`, Git Credential Manager).
    `token` is kept for API-based metrics elsewhere; it is not embedded in the clone URL.
    """
    s = repo.strip()
    key = _repo_signals_key(s)
    cached = _WORKTREE_CACHE.get(key)
    if cached and Path(cached, ".git").exists():
        return cached

    if Path(s).exists() and Path(s, ".git").exists():
        _WORKTREE_CACHE[key] = str(Path(s).resolve())
        return _WORKTREE_CACHE[key]

    owner, name = _parse_github_repo(s)
    dest = Path(tempfile.gettempdir()) / f"proxytool_wt_{owner}_{name}".replace("/", "_")
    if dest.exists() and (dest / ".git").exists():
        _WORKTREE_CACHE[key] = str(dest)
        return str(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    clean_url = _github_public_https_url(owner, name)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", clean_url, str(dest)],
            check=True,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"git clone failed for {owner}/{name} into {dest}. "
            "If this is a private repository, run `gh auth login` (or configure Git Credential "
            "Manager) so git can clone https://github.com/... without embedding a token in code. "
            "Stdout/stderr omitted to avoid leaking credentials."
        ) from None

    _WORKTREE_CACHE[key] = str(dest)
    return str(dest)


def _git_path_for_repo_signals(repo: str, token: Optional[str]) -> str:
    """Path for `git -C` (tags/branches/merges): local repo, shallow GitHub clone, or bare non-GitHub."""
    s = repo.strip()
    if Path(s).exists():
        if (Path(s) / ".git").exists() or (Path(s) / "HEAD").exists():
            return str(Path(s).resolve())

    if s.startswith("http") and not _is_github_url(s):
        return _clone_bare_for_git_log(s)

    return _ensure_shallow_worktree(s, token)


def compute_release_cadence(repo_path: str) -> Dict[str, object]:
    """Compute release cadence from git tags."""
    try:
        tags = subprocess.check_output(
            ["git", "-C", repo_path, "tag", "-l", "--sort=-v:refname"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()

        if len(tags) < 2:
            return {"num_releases": float(len(tags)), "avg_days_between": None, "has_semver": False}

        dates: List[int] = []
        for tag in tags[:30]:
            try:
                ts = subprocess.check_output(
                    ["git", "-C", repo_path, "log", "-1", "--format=%ct", tag],
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
                dates.append(int(ts))
            except Exception:
                continue

        if len(dates) < 2:
            return {"num_releases": float(len(tags)), "avg_days_between": None, "has_semver": True}

        gaps = [(dates[i] - dates[i + 1]) / 86400 for i in range(len(dates) - 1)]

        return {
            "num_releases": float(len(tags)),
            "avg_days_between": float(statistics.mean(gaps)),
            "has_semver": any(re.match(r"v?\d+\.\d+", t) for t in tags[:10]),
        }
    except Exception:
        return {"num_releases": 0.0, "avg_days_between": None, "has_semver": False}


def compute_branching_patterns(repo_path: str) -> Dict[str, object]:
    """Analyze branching and merge patterns."""
    try:
        branches = subprocess.check_output(
            ["git", "-C", repo_path, "branch", "-r"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()

        merges = subprocess.check_output(
            ["git", "-C", repo_path, "log", "--merges", "--oneline", "-n", "1000"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()

        total_commits = 1000
        merge_ratio = len(merges) / max(total_commits, 1)

        cleaned = [b.strip() for b in branches if b.strip()]
        return {
            "num_remote_branches": float(len(cleaned)),
            "merge_ratio": float(merge_ratio),
            "has_main_master": any(b in ("origin/main", "origin/master") for b in cleaned),
        }
    except Exception:
        return {"num_remote_branches": 0.0, "merge_ratio": 0.0, "has_main_master": False}


def _github_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _paged_json(url: str, headers: Dict[str, str], max_pages: int = 5) -> List[dict]:
    items: List[dict] = []
    next_url: Optional[str] = url
    pages = 0
    while next_url and pages < max_pages:
        resp = requests.get(next_url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return items
        chunk = resp.json()
        if not isinstance(chunk, list):
            return items
        items.extend(chunk)
        pages += 1

        link = resp.headers.get("Link", "")
        m = re.search(r'<([^>]+)>;\s*rel="next"', link)
        next_url = m.group(1) if m else None
        time.sleep(0.05)

    return items


def compute_issue_metrics(owner: str, repo: str, token: str) -> Dict[str, object]:
    """Compute issue/PR dynamics via GitHub API (sampled, paginated)."""
    if not token:
        return {"issue_close_rate": None, "recent_closed_count": 0.0, "total_issues_sampled": 0.0}

    headers = _github_headers(token)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100"

    try:
        issues = _paged_json(url, headers=headers, max_pages=3)
        if not issues:
            return {"issue_close_rate": None, "recent_closed_count": 0.0, "total_issues_sampled": 0.0}

        closed = [i for i in issues if i.get("closed_at")]
        return {
            "issue_close_rate": float(len(closed) / max(len(issues), 1)),
            "recent_closed_count": float(len(closed)),
            "total_issues_sampled": float(len(issues)),
        }
    except Exception:
        return {"issue_close_rate": None, "recent_closed_count": 0.0, "total_issues_sampled": 0.0}


def compute_doc_quality(repo_path: str) -> Dict[str, object]:
    """Assess documentation quality from file structure."""
    try:
        repo = Path(repo_path)
        readme = repo / "README.md"
        md_files = list(repo.rglob("*.md"))
        docs_dir = repo / "docs"

        readme_len = 0
        if readme.exists():
            readme_len = len(readme.read_text(encoding="utf-8", errors="ignore"))

        has_docs_dir = docs_dir.exists() and any(docs_dir.iterdir())

        return {
            "readme_exists": bool(readme.exists()),
            "readme_length": float(readme_len),
            "num_md_files": float(len(md_files)),
            "has_docs_dir": bool(has_docs_dir),
            "docs_score": float(min(1.0, (len(md_files) + (10 if docs_dir.exists() else 0)) / 50)),
        }
    except Exception:
        return {
            "readme_exists": False,
            "readme_length": 0.0,
            "num_md_files": 0.0,
            "has_docs_dir": False,
            "docs_score": 0.0,
        }


def compute_ci_signals(repo_path: str) -> Dict[str, object]:
    """Detect CI/CD configuration."""
    try:
        repo = Path(repo_path)
        wf_dir = repo / ".github" / "workflows"
        workflows = list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))

        ci_files: List[Path] = []
        for pat in ("*.yml", "*.yaml"):
            ci_files.extend(repo.rglob(pat))

        testish = 0
        for f in ci_files:
            n = f.name.lower()
            if any(x in n for x in ["test", "ci", "build"]):
                testish += 1

        return {
            "has_github_workflows": float(bool(workflows)),
            "num_ci_config_files": float(len(ci_files)),
            "test_related_files": float(testish),
            "ci_score": float(min(1.0, len(workflows) / 5.0)),
        }
    except Exception:
        return {
            "has_github_workflows": 0.0,
            "num_ci_config_files": 0.0,
            "test_related_files": 0.0,
            "ci_score": 0.0,
        }


class ReleaseCadenceMetric(Metric):
    name = "release_cadence"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        ctx = _repo_signals_context_active()
        if not ctx:
            return {"release_num": 0.0, "release_avg_days": 0.0, "release_has_semver": 0.0}

        d = compute_release_cadence(ctx.git_path)
        avg = d.get("avg_days_between")
        return {
            "release_num": float(d.get("num_releases", 0.0) or 0.0),
            "release_avg_days": float(avg or 0.0),
            "release_has_semver": 1.0 if bool(d.get("has_semver")) else 0.0,
        }


class BranchingMetric(Metric):
    name = "branching"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        ctx = _repo_signals_context_active()
        if not ctx:
            return {"branch_count": 0.0, "merge_ratio": 0.0, "branch_has_main_master": 0.0}

        b = compute_branching_patterns(ctx.git_path)
        return {
            "branch_count": float(b.get("num_remote_branches", 0.0) or 0.0),
            "merge_ratio": float(b.get("merge_ratio", 0.0) or 0.0),
            "branch_has_main_master": 1.0 if bool(b.get("has_main_master")) else 0.0,
        }


class IssueMetricsMetric(Metric):
    name = "issue_metrics"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        ctx = _repo_signals_context_active()
        if not ctx or not ctx.github_token:
            return {"issue_close_rate": 0.0, "issue_recent_closed": 0.0, "issue_total_sampled": 0.0}

        s = ctx.repo.strip()
        owner, name = _parse_github_repo(s)

        im = compute_issue_metrics(owner, name, ctx.github_token)
        rate = im.get("issue_close_rate")
        return {
            "issue_close_rate": float(rate or 0.0),
            "issue_recent_closed": float(im.get("recent_closed_count", 0.0) or 0.0),
            "issue_total_sampled": float(im.get("total_issues_sampled", 0.0) or 0.0),
        }


class DocQualityMetric(Metric):
    name = "doc_quality"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        ctx = _repo_signals_context_active()
        if not ctx:
            return {
                "readme_length": 0.0,
                "docs_score": 0.0,
                "doc_readme_exists": 0.0,
                "doc_num_md": 0.0,
                "doc_has_docs_dir": 0.0,
            }

        scan_root = _ensure_shallow_worktree(ctx.repo, ctx.github_token)
        d = compute_doc_quality(scan_root)
        return {
            "readme_length": float(d.get("readme_length", 0.0) or 0.0),
            "docs_score": float(d.get("docs_score", 0.0) or 0.0),
            "doc_readme_exists": 1.0 if bool(d.get("readme_exists")) else 0.0,
            "doc_num_md": float(d.get("num_md_files", 0.0) or 0.0),
            "doc_has_docs_dir": 1.0 if bool(d.get("has_docs_dir")) else 0.0,
        }


class CiSignalsMetric(Metric):
    name = "ci_signals"

    def compute(self, commits: List[CommitRecord]) -> Dict[str, float]:
        ctx = _repo_signals_context_active()
        if not ctx:
            return {"ci_score": 0.0, "ci_has_workflows": 0.0, "ci_num_configs": 0.0, "ci_testish": 0.0}

        scan_root = _ensure_shallow_worktree(ctx.repo, ctx.github_token)
        c = compute_ci_signals(scan_root)
        return {
            "ci_score": float(c.get("ci_score", 0.0) or 0.0),
            "ci_has_workflows": float(c.get("has_github_workflows", 0.0) or 0.0),
            "ci_num_configs": float(c.get("num_ci_config_files", 0.0) or 0.0),
            "ci_testish": float(c.get("test_related_files", 0.0) or 0.0),
        }

# --- notebook cell 32 (id=c54091a3) ---
ALL_METRICS = {
    "sentiment": SentimentMetric(),
    "attach": AttachRateMetric(),
    "churn": ChurnMetric(),
    "cadence": CadenceMetric(),
    "gitlogger": GitLoggerMetrics(),
    "environment": EnvironmentMetric(),
    "purpose": PurposeMetric(),
    "operational": OperationalMetric(),
    "algorithm": AlgorithmMetric(),
    "language": LanguageMetric(),
    "commitsem": CommitSemanticMetric(),
    "contributors": ContributorMetric(),
    "cochange": CochangeMetric(),
    "temporal": TemporalRhythmMetric(),
    "embedding": CommitEmbeddingMetric(),
    "release_cadence": ReleaseCadenceMetric(),
    "branching": BranchingMetric(),
    "issue_metrics": IssueMetricsMetric(),
    "doc_quality": DocQualityMetric(),
    "ci_signals": CiSignalsMetric(),
}

# --- notebook cell 33 (id=c8d1b5ef) ---

# Similarity computation: Min–max normalization, weighting, cosine similarity

class MinMaxNormalizer:
    """Scale features using a reusable fitted range.

    Why this version:
    - supports a single global fit across many repos, which stabilizes pair scores
    - keeps constant features at 0.5
    - retains the log anchor for commit_count
    """

    def __init__(self, eps: float = 0.05):
        self.min: Dict[str, float] = {}
        self.max: Dict[str, float] = {}
        self.constant_keys: set[str] = set()
        self.eps = float(eps)
        self.is_fitted = False

    def fit(self, vectors: List[Dict[str, float]]):
        keys = sorted({k for v in vectors for k in v})
        self.min = {}
        self.max = {}
        self.constant_keys = set()

        for k in keys:
            vals = [v.get(k, 0.0) for v in vectors]
            if k == "commit_count":
                vals = [math.log(max(val, 1)) for val in vals]
            mn, mx = min(vals), max(vals)
            self.min[k], self.max[k] = mn, mx
            if mx - mn <= 1e-12:
                self.constant_keys.add(k)

        self.is_fitted = True
        return self

    def transform(self, vec: Dict[str, float]) -> Dict[str, float]:
        if not self.is_fitted:
            raise RuntimeError("MinMaxNormalizer must be fit before transform().")

        out: Dict[str, float] = {}
        for k in self.min:
            if k in self.constant_keys:
                out[k] = 0.5
                continue

            val = vec.get(k, 0.0)
            if k == "commit_count":
                val = math.log(max(val, 1))

            rng = self.max[k] - self.min[k]
            z = (val - self.min[k]) / (rng if rng > 0 else 1.0)
            z = max(0.0, min(1.0, z))
            out[k] = self.eps + (1.0 - 2.0 * self.eps) * z
        return out


class MinMaxNormalizerWinsor(MinMaxNormalizer):
    """Global min–max fit with per-feature winsorization (clip to quantiles) before min/max.

    Reduces leverage of single outlier repos on a few keys when fitting ``GLOBAL_NORMALIZER``.
    """

    def __init__(self, eps: float = 0.05, q_low: float = 0.05, q_high: float = 0.95):
        super().__init__(eps=eps)
        self.q_low = float(q_low)
        self.q_high = float(q_high)

    def fit(self, vectors: List[Dict[str, float]]):
        import numpy as _np

        keys = sorted({k for v in vectors for k in v})
        self.min = {}
        self.max = {}
        self.constant_keys = set()

        for k in keys:
            vals = [float(v.get(k, 0.0)) for v in vectors]
            if k == "commit_count":
                vals = [math.log(max(val, 1)) for val in vals]
            if len(vals) < 3:
                mn, mx = min(vals), max(vals)
            else:
                lo, hi = float(_np.quantile(vals, self.q_low)), float(_np.quantile(vals, self.q_high))
                clipped = [min(max(v, lo), hi) for v in vals]
                mn, mx = min(clipped), max(clipped)
            self.min[k], self.max[k] = mn, mx
            if mx - mn <= 1e-12:
                self.constant_keys.add(k)

        self.is_fitted = True
        return self


def cosine(a: List[float], b: List[float]) -> float:
    """Standard cosine similarity between two vectors.

    Note: use built-in zip(a, b) — zip[...] is a type-annotation form and not callable.
    """
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na > 0 and nb > 0 else 0.0

def weighted_sum(vec: Dict[str, float], weights: Dict[str, float]) -> Dict[str, float]:
    """
    Apply group weights by metric family (e.g., sentiment=2.0).
    Mapping is prefix/keys-based. Defaults to 1.0 for unspecified families.
    """
    family_map = {
        "sentiment": ("sent_",),
        "cadence": ("commit_",),
        "churn": ("churn_", "lines_", "net_"),
        "attach": ("attach_rate", "issue_breadth"),
        "gitlogger": ("gl_",),
        "environment": ("env_",),
        "purpose": ("purpose_",),
        "operational": ("op_",),
        "algorithm": ("algo_",),
        "language": ("lang_",),
        "cais": ("cais_",),
        # Paper-driven metadata fingerprints
        "commitsem": ("sem_",),
        "contributors": ("contrib_",),
        "cochange": ("cochg_",),
        "temporal": ("temp_",),
        "embedding": ("emb_",),
        "release_cadence": ("release_",),
        "branching": ("branch_", "merge_ratio"),
        "issue_metrics": ("issue_",),
        "doc_quality": ("readme_length", "docs_score", "doc_"),
        "ci_signals": ("ci_",),
    }
    out: Dict[str, float] = {}
    for k, v in vec.items():
        w = 1.0
        for fam, fam_w in weights.items():
            prefixes = family_map.get(fam)
            if not prefixes:
                continue
            if any((isinstance(p, str) and k.startswith(p)) or k == p for p in prefixes):
                w = fam_w
                break
        out[k] = v * w
    return out

# --- notebook cell 36 (id=60facf5d) ---
def _parse_github_repo(repo: str) -> Tuple[str, str]:
    """
    Accepts:
      - https://github.com/owner/name(.git)
      - owner/name(.git)
    Returns (owner, name) or raises ValueError on invalid input.
    """
    s = repo.strip()
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)", s)
    if m:
        return m.group(1), m.group(2).removesuffix(".git")
    if "/" in s:
        owner, name = s.split("/", 1)
        return owner, name.removesuffix(".git")
    raise ValueError(f"Not a valid GitHub repository spec: {repo}")


_BARE_CLONE_CACHE: Dict[str, str] = {}

def _clone_bare_for_git_log(url: str, depth: int = 200) -> str:
    """Shallow bare clone of a non-GitHub git URL. Cached per URL."""
    if url in _BARE_CLONE_CACHE:
        cached = _BARE_CLONE_CACHE[url]
        if Path(cached).exists():
            return cached
    import tempfile, hashlib
    slug = hashlib.sha256(url.encode()).hexdigest()[:12]
    dest = Path(tempfile.gettempdir()) / f"proxytool_bare_{slug}"
    if dest.exists() and (dest / "HEAD").exists():
        _BARE_CLONE_CACHE[url] = str(dest)
        return str(dest)
    _log(f"  Shallow clone (depth={depth}) {url} ...", "info")
    subprocess.run(
        ["git", "clone", "--bare", "--filter=blob:none", f"--depth={depth}", url, str(dest)],
        check=True, capture_output=True, text=True, timeout=180,
    )
    _BARE_CLONE_CACHE[url] = str(dest)
    return str(dest)


def _is_github_url(repo: str) -> bool:
    return bool(re.match(r"https?://github\.com/", repo.strip()))


def compute_features_for_repo(
    repo: str,
    metric_names: List[str],
    since: Optional[str],
    until: Optional[str],
    github_token: Optional[str],
    max_commits: Optional[int] = None
) -> Dict[str, float]:
    try:
        if repo.startswith("http") and not _is_github_url(repo):
            bare_path = _clone_bare_for_git_log(repo)
            commits = run_git_log(bare_path, since, until, max_commits)
        elif repo.startswith("http") or ("/" in repo and not Path(repo).exists()):
            owner, name = _parse_github_repo(repo)
            commits = run_github_log(owner, name, github_token, since, until, max_commits)
        else:
            commits = run_git_log(repo, since, until, max_commits)
    except Exception as e:
        _log(f"  Failed to fetch {repo}: {e}", "info")
        commits = []

    # Always compute cadence first (commit_count is anchor for similarity)
    features: Dict[str, float] = {}
    cadence = CadenceMetric().compute(commits)
    features.update(cadence)
    _log(f"  [DEBUG] Fetched {len(commits)} commits, commit_count={cadence.get('commit_count')}", "debug")

    git_path = _git_path_for_repo_signals(repo, github_token)

    # Add all requested metrics (safe to re-add cadence)
    with repo_signals_context(RepoSignalsContext(repo=repo, github_token=github_token, git_path=git_path)):
        for name in metric_names:
            if name not in ALL_METRICS:
                raise KeyError(f"Unknown metric: {name}")
            features.update(ALL_METRICS[name].compute(commits))

    return features

# --- notebook cell 38 (id=dfd540c4) ---

class MinMaxNormalizer:
    """
    Scale features using a reusable fitted range.

    Supports both local min-max normalization (fit on the current comparison set)
    and global min-max normalization (fit once on a representative corpus).
    """
    def __init__(self, eps: float = 0.05):
        self.min: Dict[str, float] = {}
        self.max: Dict[str, float] = {}
        self.constant_keys: set[str] = set()
        self.eps = float(eps)
        self.is_fitted = False

    def fit(self, vectors: List[Dict[str, float]]):
        keys = sorted({k for v in vectors for k in v})
        self.min = {}
        self.max = {}
        self.constant_keys = set()

        for k in keys:
            vals = [v.get(k, 0.0) for v in vectors]
            if k == "commit_count":
                vals = [math.log(max(val, 1)) for val in vals]
            mn, mx = min(vals), max(vals)
            self.min[k], self.max[k] = mn, mx
            if mx - mn <= 1e-12:
                self.constant_keys.add(k)

        self.is_fitted = True
        return self

    def transform(self, vec: Dict[str, float]) -> Dict[str, float]:
        if not self.is_fitted:
            raise RuntimeError("MinMaxNormalizer must be fit before transform().")

        out: Dict[str, float] = {}
        for k in self.min:
            if k in self.constant_keys:
                out[k] = 0.5
                continue

            val = vec.get(k, 0.0)
            if k == "commit_count":
                val = math.log(max(val, 1))

            rng = self.max[k] - self.min[k]
            z = (val - self.min[k]) / (rng if rng > 0 else 1.0)
            z = max(0.0, min(1.0, z))
            out[k] = self.eps + (1.0 - 2.0 * self.eps) * z
        return out


class MinMaxNormalizerWinsor(MinMaxNormalizer):
    """Global min–max fit with per-feature winsorization before min/max (see REDUX_4 plan)."""

    def __init__(self, eps: float = 0.05, q_low: float = 0.05, q_high: float = 0.95):
        super().__init__(eps=eps)
        self.q_low = float(q_low)
        self.q_high = float(q_high)

    def fit(self, vectors: List[Dict[str, float]]):
        import numpy as _np

        keys = sorted({k for v in vectors for k in v})
        self.min = {}
        self.max = {}
        self.constant_keys = set()

        for k in keys:
            vals = [float(v.get(k, 0.0)) for v in vectors]
            if k == "commit_count":
                vals = [math.log(max(val, 1)) for val in vals]
            if len(vals) < 3:
                mn, mx = min(vals), max(vals)
            else:
                lo, hi = float(_np.quantile(vals, self.q_low)), float(_np.quantile(vals, self.q_high))
                clipped = [min(max(v, lo), hi) for v in vals]
                mn, mx = min(clipped), max(clipped)
            self.min[k], self.max[k] = mn, mx
            if mx - mn <= 1e-12:
                self.constant_keys.add(k)

        self.is_fitted = True
        return self



class ZScoreNormalizer:
    """
    Standardize features using global or local mean / standard deviation.

    Why add this:
    - metadata families often live on very different natural scales
    - z-score scaling is less tied to observed min/max extremes
    - it gives a cleaner side-by-side alternative to min-max for ablation
    """
    def __init__(self, clip: float = 3.0):
        self.mean: Dict[str, float] = {}
        self.std: Dict[str, float] = {}
        self.constant_keys: set[str] = set()
        self.clip = float(clip)
        self.is_fitted = False

    def fit(self, vectors: List[Dict[str, float]]):
        keys = sorted({k for v in vectors for k in v})
        self.mean = {}
        self.std = {}
        self.constant_keys = set()

        for k in keys:
            vals = [v.get(k, 0.0) for v in vectors]
            if k == "commit_count":
                vals = [math.log(max(val, 1)) for val in vals]
            arr = np.array(vals, dtype=float)
            mu = float(np.mean(arr))
            sigma = float(np.std(arr))
            self.mean[k], self.std[k] = mu, sigma
            if sigma <= 1e-12:
                self.constant_keys.add(k)

        self.is_fitted = True
        return self

    def transform(self, vec: Dict[str, float]) -> Dict[str, float]:
        if not self.is_fitted:
            raise RuntimeError("ZScoreNormalizer must be fit before transform().")

        out: Dict[str, float] = {}
        for k in self.mean:
            if k in self.constant_keys:
                out[k] = 0.0
                continue

            val = vec.get(k, 0.0)
            if k == "commit_count":
                val = math.log(max(val, 1))

            sigma = self.std[k] if self.std[k] > 0 else 1.0
            z = (val - self.mean[k]) / sigma
            z = max(-self.clip, min(self.clip, z))
            out[k] = z / self.clip
        return out


GLOBAL_NORMALIZER = None
GLOBAL_ZSCORE_NORMALIZER = None

# Main experimental path. Override per call when needed.
DEFAULT_NORMALIZATION_MODE = "global_minmax"


def clear_global_normalizers():
    global GLOBAL_NORMALIZER, GLOBAL_ZSCORE_NORMALIZER
    GLOBAL_NORMALIZER = None
    GLOBAL_ZSCORE_NORMALIZER = None


def fit_global_normalizer(
    repo_urls: List[str],
    metrics: str = None,
    token: Optional[str] = None,
    max_commits: int = 150,
    strategy: str = "minmax",
):
    """Fit one reusable normalizer over a representative repo pool."""
    global GLOBAL_NORMALIZER, GLOBAL_ZSCORE_NORMALIZER
    token = token or github_token
    metrics_list = [m.strip() for m in (metrics or CAIS_METRICS).split(",")]

    vecs: List[Dict[str, float]] = []
    for r in repo_urls:
        try:
            vec = compute_features_for_repo(r, metrics_list, None, None, token, max_commits)
            if vec:
                vecs.append(vec)
        except Exception:
            pass

    if not vecs:
        raise RuntimeError(
            f"fit_global_normalizer could not compute any feature vectors "
            f"(tried {len(repo_urls)} repo(s); check URL shape owner/repo or https://github.com/..., "
            f"GitHub token, and network)."
        )

    if strategy == "minmax":
        GLOBAL_NORMALIZER = MinMaxNormalizer().fit(vecs)
    elif strategy == "minmax_winsor":
        GLOBAL_NORMALIZER = MinMaxNormalizerWinsor().fit(vecs)
        print(f"Global winsorized min-max normalizer fit on {len(vecs)} repos")
        print(f"Global min-max normalizer fit on {len(vecs)} repos")
        return GLOBAL_NORMALIZER
    elif strategy == "zscore":
        GLOBAL_ZSCORE_NORMALIZER = ZScoreNormalizer().fit(vecs)
        print(f"Global z-score normalizer fit on {len(vecs)} repos")
        return GLOBAL_ZSCORE_NORMALIZER
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def fit_global_zscore_normalizer(
    repo_urls: List[str],
    metrics: str = None,
    token: Optional[str] = None,
    max_commits: int = 150,
):
    return fit_global_normalizer(
        repo_urls=repo_urls,
        metrics=metrics,
        token=token,
        max_commits=max_commits,
        strategy="zscore",
    )

# --- notebook cell 41 (id=200b5b58) ---
def _short_repo(r: str) -> str:
    parts = r.rstrip("/").split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else r


def _parse_figsize(s: Optional[str]) -> Tuple[float, float]:
    if not s:
        return (max(6.0, 0.7 * 4), 4.5)
    m = re.match(r"^\s*(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)\s*$", s)
    if not m:
        return (8.0, 4.5)
    return (float(m.group(1)), float(m.group(2)))


def _annotate_bars(ax, rects, horizontal=False):
    for r in rects:
        val = r.get_width() if horizontal else r.get_height()
        if horizontal:
            ax.text(val + 0.01, r.get_y() + r.get_height()/2.0, f"{val:.3f}", va="center")
        else:
            ax.text(r.get_x() + r.get_width()/2.0, val + 0.01, f"{val:.3f}", ha="center")

# --- notebook cell 42 (id=c6c0fd1a) ---
def plot_similarities(ranked: List[Tuple[str, float]], query: str, out_path: str, dpi: int = 200, fig_size: Optional[str] = None):
    """
    Save a summary chart of candidate cosine similarities.
    • Single candidate -> horizontal gauge-style bar with value label
    • Multiple candidates -> vertical bars with y∈[0,1], grid, and labels
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # headless
        import matplotlib.pyplot as plt
    except Exception as e:
        _log(f"[Plot] matplotlib unavailable: {e}", "info")
        return

    labels = [_short_repo(repo) for repo, _ in ranked]
    vals = [float(sim) for _, sim in ranked]

    w, h = _parse_figsize(fig_size)
    plt.figure(figsize=(w, h))
    ax = plt.gca()

    if len(vals) == 1:
        # Horizontal gauge for a single bar
        rects = ax.barh([0], [vals[0]], height=0.35)
        ax.set_xlim(0, 1)
        ax.set_yticks([0])
        ax.set_yticklabels([labels[0]])
        ax.set_xlabel("Cosine similarity")
        ax.set_title(f"Similarity vs. query: {_short_repo(query)}")
        ax.grid(axis="x", alpha=0.3)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        _annotate_bars(ax, rects, horizontal=True)
    else:
        # Vertical bars for multiple candidates
        xs = range(len(vals))
        rects = ax.bar(xs, vals)
        ax.set_ylim(0, 1)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_ylabel("Cosine similarity")
        ax.set_title(f"Similarity vs. query: {_short_repo(query)}")
        ax.grid(axis="y", alpha=0.3)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        _annotate_bars(ax, rects, horizontal=False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi)
    plt.close()
    _log(f"[Plot] Saved similarity chart to {out_path}", "info")

# --- notebook cell 43 (id=9c9d89c8) ---
def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


def plot_feature_contribs(q_vec: List[float], cand_vec: List[float], keys: List[str],
                          title: str, out_path: str, topn: int = 10, dpi: int = 200):
    """
    Save a horizontal bar chart of the top-k feature contributions to similarity.

    Contribution proxy ≈ q[k] * cand[k] (cosine numerator). We rank by absolute
    contribution magnitude so the most influential features (positive or negative)
    appear at the top. Bars can be negative if a feature pushes similarity down.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        _log(f"[Plot] matplotlib unavailable for feature contributions: {e}", "info")
        return

    contribs = [(k, q * c) for k, q, c in zip(keys, q_vec, cand_vec)]
    contribs.sort(key=lambda x: abs(x[1]), reverse=True)
    top = contribs[:max(1, topn)]
    labels = [k for k, _ in top][::-1]
    vals = [v for _, v in top][::-1]

    total_abs = sum(abs(v) for v in vals) or 1.0
    shares = [v / total_abs for v in vals]  # signed share of |top| total

    plt.figure(figsize=(9, max(3.5, 0.5 * len(labels) + 1)))
    ax = plt.gca()
    rects = ax.barh(range(len(shares)), shares)
    ax.set_yticks(range(len(shares)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Contribution share to cosine similarity (signed)")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    # annotate values
    for i, v in enumerate(shares):
        ax.text(v + (0.01 if v >= 0 else -0.01), i, f"{v:+.3f}", va="center",
                ha="left" if v >= 0 else "right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi)
    plt.close()
    _log(f"[Plot] Saved feature contributions chart to {out_path}", "info")

# --- notebook cell 46 (id=62c92295) ---
# Configure output directory for plots
PLOTS_DIR = Path("results_plots")  # Change this to your preferred folder name


def ensure_plots_directory():
    """Create the plots directory if it doesn't exist."""
    PLOTS_DIR.mkdir(exist_ok=True)
    return PLOTS_DIR


def organize_plot_path(filename: str) -> str:
    """
    Organize plot into a dedicated directory.
    Takes a filename and returns the full path within the plots directory.
    """
    ensure_plots_directory()
    return str(PLOTS_DIR / filename)


def display_plot_inline(image_path: str):
    """
    Display a saved plot inline in Jupyter notebook.
    This is a helper function that doesn't modify the core plotting logic.
    """
    try:
        from IPython.display import Image, display
        display(Image(filename=image_path))
    except Exception:
        # Fallback: just print the path
        print(f"Plot saved to: {image_path}")


def plot_and_show(
    ranked: list,
    query: str,
    out_path: str,
    dpi: int = 200,
    fig_size: str = None,
    organized: bool = True
):
    """
    Wrapper that calls original plot_similarities and displays inline.
    Preserves original function - just adds display functionality.
    
    Args:
        organized: If True, saves plots to PLOTS_DIR folder (default: True)
    """
    # Organize path if requested
    if organized:
        out_path = organize_plot_path(Path(out_path).name)
    
    # Call original function (unchanged)
    plot_similarities(ranked, query, out_path, dpi, fig_size)
    # Then display inline
    display_plot_inline(out_path)


def plot_features_and_show(q_vec, cand_vec, keys, title, out_path, topn=10, dpi=200, organized=True):
    """
    Wrapper that calls original plot_feature_contribs and displays inline.
    Preserves original function - just adds display functionality.
    
    Args:
        organized: If True, saves plots to PLOTS_DIR folder (default: True)
    """
    # Organize path if requested
    if organized:
        out_path = organize_plot_path(Path(out_path).name)
    
    # Call original function (unchanged)
    plot_feature_contribs(q_vec, cand_vec, keys, title, out_path, topn, dpi)
    # Then display inline
    display_plot_inline(out_path)

# --- notebook cell 48 (id=61d99933) ---
def parse_weights(s: Optional[str]) -> Dict[str, float]:
    if not s:
        return {}
    out: Dict[str, float] = {}
    for part in s.split(","):
        k, _, v = part.partition("=")
        if _:
            out[k.strip()] = float(v.strip())
    return out


def _slug_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")


def load_cais_profile(path: Optional[str]) -> Dict[str, float]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    features: Dict[str, float] = {}

    for k in ("O1", "O3", "O4", "O5"):
        if k in data:
            val = float(data[k])
            # O3/O4/O5 commonly provided on 0-9 scale in NIST examples.
            if k in ("O3", "O4", "O5"):
                val = max(0.0, min(val, 9.0)) / 9.0
            features[f"cais_{k.lower()}"] = val

    o2 = str(data.get("O2", "")).strip()
    if o2:
        for idx, ch in enumerate(o2[:5], start=1):
            features[f"cais_o2_bit_{idx}"] = 1.0 if ch == "1" else 0.0

    env = _slug_key(str(data.get("operational_environment", "")))
    if env:
        features[f"env_{env}"] = 1.0

    for p in data.get("application_purpose", []) or []:
        sk = _slug_key(str(p))
        if sk:
            features[f"purpose_{sk}"] = 1.0

    for a in data.get("ml_algorithms", []) or []:
        sk = _slug_key(str(a))
        if sk:
            features[f"algo_{sk}"] = 1.0

    dev = data.get("dev_techniques", {}) or {}
    for lang in dev.get("languages", []) or []:
        sk = _slug_key(str(lang))
        if sk:
            features[f"lang_{sk}"] = 1.0

    proc = _slug_key(str(dev.get("process", "")))
    if proc:
        features[f"cais_process_{proc}"] = 1.0

    return features

# --- notebook cell 49 (id=91607d7b) ---
def cmd_compare(args):
    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else ["sentiment"]
    weights = parse_weights(args.weights)
    repos = [args.query] + args.candidates
    cais_features = load_cais_profile(getattr(args, "cais_profile", None))

    _log(f"Comparing {len(args.candidates)} candidate(s) using: {', '.join(metrics)}", "info")
    if weights:
        _log(f"  Weights: {weights}", "info")
    if cais_features:
        _log(f"  CAIS profile loaded: {len(cais_features)} anchored features", "info")
    _log("", "info")

    vecs: List[Dict[str, float]] = []
    for i, r in enumerate(repos):
        label = "QUERY" if i == 0 else f"CANDIDATE {i}"
        _log(f"[{label}] {_short_repo(r)}", "info")
        start = time.time()
        try:
            vec = compute_features_for_repo(r, metrics, args.since, args.until, args.github_token, args.max_commits)
            if i == 0 and cais_features:
                # Anchor query with explicit CAIS taxonomy profile (O1-O5 + dimension tags).
                vec.update(cais_features)
            elapsed = time.time() - start
            count = vec.get("commit_count", 0)
            _log(f"  Done ({int(count)} commits, {elapsed:.1f}s)\n", "info")
            _log(f"  [DEBUG] Features ({len(vec)}): {sorted(vec.keys())}", "debug")
            vecs.append(vec)
        except Exception as e:
            _log(f"  FAILED ({time.time() - start:.1f}s): {e}\n", "info")
            vecs.append({})

    if len(vecs) < 2 or not any(vecs):
        _log("Not enough data.", "info")
        return

    _log("Normalizing...", "info")
    norm = _get_normalizer_for_mode(getattr(args, "normalization_mode", DEFAULT_NORMALIZATION_MODE), vecs)
    normed = [norm.transform(v) for v in vecs]
    normed_w = [weighted_sum(v, weights) for v in normed]

    # Ensure commit_count exists in all vectors (anchor feature)
    for v in normed_w:
        v["commit_count"] = v.get("commit_count", 0.0)

    # Use only COMMON features across all repos
    if len(normed_w) > 1:
        common_keys = set(normed_w[0].keys())
        for v in normed_w[1:]:
            common_keys &= v.keys()
        keys = sorted(common_keys)
    else:
        keys = sorted(normed_w[0].keys()) if normed_w else []

    if not keys:
        _log(" No common features. Cannot compute similarity.", "info")
        return

    embs = [[v.get(k, 0.0) for k in keys] for v in normed_w]
    q_emb = embs[0]
    _log(" Done\n", "info")

    ranked = [(repo, cosine(q_emb, emb)) for repo, emb in zip(args.candidates, embs[1:])]
    ranked.sort(key=lambda x: x[1], reverse=True)

    print("=" * 70)
    print(f"QUERY: {args.query}")
    print(f"METRICS: {', '.join(metrics)}")
    if weights:
        print(f"WEIGHTS: {weights}")
    print("=" * 70)
    print("TOP MATCHES:")
    for i, (repo, sim) in enumerate(ranked[:10], 1):
        print(f" {i:2d}. {_short_repo(repo):<40} -> similarity = {sim:.4f}")
    if len(ranked) > 10:
        print(f" ... and {len(ranked) - 10} more")
    print("=" * 70)

    # Optional plots
    if args.plot is not None:
        out_path = args.plot if isinstance(args.plot, str) else "similarity.png"
        #plot_similarities(ranked, args.query, out_path, dpi=args.dpi, fig_size=args.plot_size)
        # Use wrapper function for inline display in notebooks
        plot_and_show(ranked, args.query, out_path, dpi=args.dpi, fig_size=args.plot_size)

        # Detailed per-candidate feature contributions
        if args.plot_details:
            base = Path(out_path)
            for (repo, _), emb in zip(ranked, embs[1:]):
                title = f"Top features vs. {_short_repo(args.query)} — {_short_repo(repo)}"
                fname = base.with_name(f"{base.stem}__features__{_slug(_short_repo(repo))}{base.suffix}")
                #plot_feature_contribs(q_emb, emb, keys, title, str(fname), topn=args.topn_features, dpi=args.dpi)
                plot_features_and_show(q_emb, emb, keys, title, str(fname), topn=args.topn_features, dpi=args.dpi)

# --- notebook cell 50 (id=aa6e55bd) ---

# Helpers for CAIS suite: must run after cmd_compare (and its deps) and before any cell that uses them.
from typing import Dict, List, Optional, Tuple
from types import SimpleNamespace
from pathlib import Path
import json
import numpy as np
from tempfile import TemporaryDirectory


def _write_profile_json(profile: Dict[str, object], tmp_dir: str) -> str:
    path = Path(tmp_dir) / "cais_profile.json"
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return str(path)


def _build_compare_args(
    query: str,
    candidates: List[str],
    metrics: str,
    cais_profile_path: Optional[str],
    since: Optional[str] = None,
    until: Optional[str] = None,
    max_commits: Optional[int] = 150,
    weights: Optional[str] = None,
    normalization_mode: Optional[str] = None,
    pairwise_scoring: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        query=query,
        candidates=candidates,
        metrics=metrics,
        weights=weights,
        cais_profile=cais_profile_path,
        since=since,
        until=until,
        github_token=github_token,
        max_commits=max_commits,
        normalization_mode=normalization_mode,
        pairwise_scoring=pairwise_scoring,
        plot=None,
        plot_details=False,
        plot_size=None,
        dpi=200,
        topn_features=10,
        quiet=False,
        verbose=True,
    )


def _get_normalizer_for_mode(
    mode: Optional[str],
    vecs: List[Dict[str, float]],
):
    mode = mode or DEFAULT_NORMALIZATION_MODE

    if mode == "local_minmax":
        return MinMaxNormalizer().fit(vecs)
    if mode == "global_minmax":
        return GLOBAL_NORMALIZER if GLOBAL_NORMALIZER is not None else MinMaxNormalizer().fit(vecs)
    if mode == "local_zscore":
        return ZScoreNormalizer().fit(vecs)
    if mode == "global_zscore":
        return GLOBAL_ZSCORE_NORMALIZER if GLOBAL_ZSCORE_NORMALIZER is not None else ZScoreNormalizer().fit(vecs)

    raise ValueError(f"Unknown normalization mode: {mode}")


def _vectorize_repo_set(
    repos: List[str],
    metrics: List[str],
    github_token: Optional[str],
    max_commits: int,
    since: Optional[str] = None,
    until: Optional[str] = None,
    cais_features: Optional[Dict[str, object]] = None,
    normalization_mode: Optional[str] = None,
    weights: Optional[str] = None,
) -> Tuple[List[np.ndarray], List[str]]:
    parsed_weights = parse_weights(weights)
    vecs: List[Dict[str, float]] = []

    for i, r in enumerate(repos):
        try:
            vec = compute_features_for_repo(r, metrics, since, until, github_token, max_commits)
            if i == 0 and cais_features:
                vec.update(cais_features)
            vecs.append(vec)
        except Exception:
            vecs.append({})

    if len(vecs) < 2 or not any(vecs):
        return [], []

    norm = _get_normalizer_for_mode(normalization_mode, vecs)
    normed = [norm.transform(v) for v in vecs]
    normed_w = [weighted_sum(v, parsed_weights) for v in normed]
    for v in normed_w:
        v["commit_count"] = v.get("commit_count", 0.0)

    common_keys = set(normed_w[0].keys())
    for v in normed_w[1:]:
        common_keys &= v.keys()
    keys = sorted(common_keys)
    if not keys:
        return [], []

    embs = []
    for v in normed_w:
        arr = np.array([v.get(k, 0.0) for k in keys], dtype=float)
        nrm = np.linalg.norm(arr)
        embs.append(arr / nrm if nrm > 0 else arr)
    return embs, keys


def get_ranked_similarity(args: SimpleNamespace) -> Optional[List[Tuple[str, float]]]:
    """Run the same pipeline as cmd_compare but return [(repo, sim), ...] without printing."""
    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else ["sentiment"]
    repos = [args.query] + args.candidates
    cais_features = load_cais_profile(getattr(args, "cais_profile", None))

    embs, keys = _vectorize_repo_set(
        repos=repos,
        metrics=metrics,
        github_token=args.github_token,
        max_commits=args.max_commits,
        since=args.since,
        until=args.until,
        cais_features=cais_features,
        normalization_mode=getattr(args, "normalization_mode", DEFAULT_NORMALIZATION_MODE),
        weights=args.weights,
    )
    if not embs or not keys:
        return None

    q = embs[0]
    ranked = []
    for i, r in enumerate(repos[1:], start=1):
        sim = float(np.dot(q, embs[i])) if q.size and embs[i].size else 0.0
        ranked.append((r, sim))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def get_pairwise_similarity(args: SimpleNamespace) -> Optional[List[Tuple[str, float]]]:
    """
    Score each candidate against the query in an isolated pairwise comparison.

    Why this matters:
    - the score for query vs target should not depend on which other negatives
      happen to be present in the candidate set
    - this is the cleanest way to test metadata against traditional methods
    """
    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else ["sentiment"]
    cais_features = load_cais_profile(getattr(args, "cais_profile", None))

    ranked = []
    for cand in args.candidates:
        repos = [args.query, cand]
        embs, keys = _vectorize_repo_set(
            repos=repos,
            metrics=metrics,
            github_token=args.github_token,
            max_commits=args.max_commits,
            since=args.since,
            until=args.until,
            cais_features=cais_features,
            normalization_mode=getattr(args, "normalization_mode", DEFAULT_NORMALIZATION_MODE),
            weights=args.weights,
        )
        if not embs or not keys:
            ranked.append((cand, 0.0))
            continue

        q = embs[0]
        c = embs[1]
        sim = float(np.dot(q, c)) if q.size and c.size else 0.0
        ranked.append((cand, sim))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked

# --- notebook cell 51 (id=ad562d7e) ---
def build_parser():
    p = argparse.ArgumentParser(description="Metadata-only repo similarity", formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("compare", help="Compare repos")
    cp.add_argument("--query", required=True)
    cp.add_argument("--candidates", nargs="+", required=True)
    cp.add_argument("--metrics", default="sentiment")
    cp.add_argument("--weights", help="e.g., sentiment=2.0,churn=0.5")
    cp.add_argument("--cais-profile", help="Path to CAIS taxonomy JSON profile (O1-O5 + dimension tags)")
    cp.add_argument("--since", help="YYYY-MM-DD")
    cp.add_argument("--until", help="YYYY-MM-DD")
    cp.add_argument("--github-token", help="GitHub PAT")
    cp.add_argument("--max-commits", type=int, help="Limit commits per repo (for testing)")
    cp.add_argument("--plot", nargs="?", const="similarity.png",
                    help="Save a summary chart of candidate similarities to PATH (default: similarity.png)")
    cp.add_argument("--plot-details", action="store_true",
                    help="Also save per-candidate 'top feature contributions' charts")
    cp.add_argument("--plot-size", help='Figure size for summary plot in "WxH" inches, e.g., 8x4 (auto if omitted)')
    cp.add_argument("--dpi", type=int, default=200, help="DPI for plots (default 200)")
    cp.add_argument("--topn-features", type=int, default=10, help="Top-N features in detail charts (default 10)")
    cp.add_argument("--quiet", action="store_true", help="Reduce output; hides cache/progress/debug logs")
    cp.add_argument("--verbose", action="store_true", help="Enable debug logs")
    cp.set_defaults(func=cmd_compare)

    return p


def main():
    global VERBOSE, QUIET
    parser = build_parser()
    args = parser.parse_args()
    VERBOSE = bool(args.verbose)
    QUIET = bool(args.quiet)
    args.func(args)

# --- notebook cell 55 (id=cfff1f38) ---
# Example: Disable inline display (only save files, don't show in notebook)
from types import SimpleNamespace

args_no_display = SimpleNamespace(
    query="https://github.com/microsoft/vscode",
    candidates=["https://github.com/facebook/react"],
    metrics=CAIS_METRICS,
    weights=None,
    since=None,
    until=None,
    github_token=github_token,
    max_commits=100,
    plot="results_batch.png",
    plot_details=False,
    plot_size=None,
    dpi=200,
    topn_features=10,
    quiet=False,
    verbose=False,
    display_inline=False  # <-- Set to False to skip inline display
)

# This will only save the plot, not display it in the notebook
# cmd_compare(args_no_display)

# --- notebook cell 107 (id=9b1faa9e) ---

from types import SimpleNamespace
import os

# Base and CAIS metrics are defined near the top of the notebook.
BASE_METRICS = BASE_METRICS
CAIS_METRICS = CAIS_METRICS

# Reweighted profiles tuned to reduce reliance on commit-message wording
# and emphasize structural / behavioral metadata.
CAIS_WEIGHTS = (
    "sentiment=0.35,cadence=1.05,churn=1.25,attach=0.50,gitlogger=1.20,"
    "environment=0.55,purpose=0.55,operational=0.60,algorithm=0.55,language=1.20,"
    "commitsem=0.65,contributors=0.30,cochange=1.75,temporal=1.25,embedding=0.80,release_cadence=0.55,branching=0.55,issue_metrics=0.45,doc_quality=0.35,ci_signals=0.65"
)

CAIS_WEIGHTS_MIMIC = (
    "sentiment=0.25,cadence=1.55,churn=0.95,attach=0.80,gitlogger=1.25,"
    "environment=0.40,purpose=0.40,operational=0.45,algorithm=0.40,language=0.80,"
    "commitsem=0.15,contributors=0.60,cochange=1.50,temporal=1.75,embedding=0.25,release_cadence=0.55,branching=0.55,issue_metrics=0.45,doc_quality=0.35,ci_signals=0.65"
)

CAIS_WEIGHTS_1 = (
    "sentiment=0.55,cadence=0.35,churn=0.95,attach=0.30,gitlogger=0.35,"
    "environment=0.25,purpose=0.25,operational=0.30,algorithm=0.40,language=0.20,"
    "commitsem=1.35,contributors=0.40,cochange=1.15,temporal=0.45,embedding=1.30,release_cadence=0.55,branching=0.55,issue_metrics=0.45,doc_quality=0.35,ci_signals=0.65"
)

CAIS_WEIGHTS_STRICT = (
    "sentiment=0.40,cadence=0.45,churn=0.85,attach=0.45,gitlogger=0.40,"
    "environment=0.35,purpose=0.35,operational=0.40,algorithm=0.45,language=0.30,"
    "commitsem=0.90,contributors=0.55,cochange=0.95,temporal=0.55,embedding=0.85,release_cadence=0.55,branching=0.55,issue_metrics=0.45,doc_quality=0.35,ci_signals=0.65"
)

# REDUX_3 tuning defaults
REDUX3_COVERAGE_PENALTY_LAMBDA = 0.20
REDUX3_METADATA_WINDOWS = [50, 150]
REDUX3_WINDOW_WEIGHTS = {50: 0.65, 150: 0.35}
REDUX3_DEFAULT_REPORTING_BENCHMARK = "contrastive"
REDUX3_DEFAULT_REPORTING_RETRIEVAL = "rank_pct"
REDUX3_DOMAIN_NEGATIVE_LIMIT = 12


def _weights_to_dict(weights: str) -> Dict[str, float]:
    return {k: float(v) for k, v in parse_weights(weights).items()}


def _dict_to_weights(d: Dict[str, float]) -> str:
    return ",".join(f"{k}={float(v):.6g}" for k, v in sorted(d.items()))


def blend_weight_profiles(alpha_strict: float = 0.7, alpha_mimic: float = 0.3, alpha_one: float = 0.0) -> str:
    """Convex blend of strict/mimic/1 profiles. Coefficients are normalized if needed."""
    coeffs = np.array([alpha_strict, alpha_mimic, alpha_one], dtype=float)
    coeffs = np.clip(coeffs, 0.0, None)
    if float(coeffs.sum()) <= 1e-12:
        coeffs = np.array([1.0, 0.0, 0.0], dtype=float)
    coeffs = coeffs / float(coeffs.sum())

    src = [_weights_to_dict(CAIS_WEIGHTS_STRICT), _weights_to_dict(CAIS_WEIGHTS_MIMIC), _weights_to_dict(CAIS_WEIGHTS_1)]
    keys = sorted(set().union(*[set(s.keys()) for s in src]))
    out: Dict[str, float] = {}
    for k in keys:
        out[k] = float(coeffs[0] * src[0].get(k, 0.0) + coeffs[1] * src[1].get(k, 0.0) + coeffs[2] * src[2].get(k, 0.0))
    return _dict_to_weights(out)


CAIS_WEIGHTS_REDUX3_BLEND = blend_weight_profiles(0.7, 0.3, 0.0)

# Use github_token from the config cell above.

CAIS_RUBRIC = {
    "O1": {
        "description": "Autonomy level",
        "scale": "0=assistive/human-in-the-loop, 1=autonomous closed-loop",
    },
    "O2": {
        "description": "Operational attribute flags (5-bit string)",
        "bits": {
            "bit_1": "real-time control constraint",
            "bit_2": "safety-critical actuation",
            "bit_3": "open-world sensing uncertainty",
            "bit_4": "mission/adaptation under uncertainty",
            "bit_5": "human override / supervisory coordination",
        },
    },
    "O3": {
        "description": "Learning regime",
        "scale": "0=rule-based/static, 1=offline trained, 2=online/adaptive",
    },
    "O4": {
        "description": "Deployment context",
        "scale": "0=enterprise/back-office, 1=embedded/edge/robotic/real-time",
    },
    "O5": {
        "description": "Consequence severity",
        "scale": "0=low, 1=moderate, 2=high-stakes/safety-critical",
    },
}

CAIS_DOMAIN_CONFIGS = {
    "autonomous_driving": {
        "query": "https://github.com/commaai/openpilot",
        "candidates": [
            "https://github.com/autowarefoundation/autoware",
            "https://github.com/ApolloAuto/apollo",
            "https://github.com/ArduPilot/ardupilot",
            "https://github.com/django/django",
            "https://github.com/expressjs/express",
            "https://github.com/rust-lang/rust",
        ],
        "expected_high_similarity": ["autoware", "apollo"],
        "controls": ["django", "express", "rust"],
        "profile": {
            "O1": 1, "O2": "11111", "O3": 8, "O4": 8, "O5": 9,
            "operational_environment": "land",
            "application_purpose": ["planning", "perception", "vehicles", "robotics"],
            "ml_algorithms": ["deep_learning", "reinforcement"],
            "dev_techniques": {"languages": ["python", "cpp"], "process": "agile"},
        },
        "justification": "Autonomous road control has real-time actuation, high mission criticality, and very high human-safety exposure.",
        "source_refs": ["CAIS taxonomy (5 dimensions)", "NIST CSWP 31 operational risk framing"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "medical_ai": {
        "query": "https://github.com/Project-MONAI/MONAI",
        "candidates": [
            "https://github.com/microsoft/InnerEye-DeepLearning",
            "https://github.com/pytorch/pytorch",
            "https://github.com/tensorflow/tensorflow",
            "https://github.com/electron/electron",
            "https://github.com/django/django",
            "https://github.com/pallets/flask",
        ],
        "expected_high_similarity": ["innereye", "pytorch", "tensorflow"],
        "controls": ["electron", "django", "flask"],
        "profile": {
            "O1": 0, "O2": "10111", "O3": 6, "O4": 8, "O5": 9,
            "operational_environment": "medical",
            "application_purpose": ["learning", "perception", "reasoning"],
            "ml_algorithms": ["deep_learning", "regression"],
            "dev_techniques": {"languages": ["python"], "process": "agile"},
        },
        "justification": "Clinical AI is typically assistive but errors produce high social and life-safety consequences.",
        "source_refs": ["CAIS taxonomy environment/purpose", "NIST CSWP 31 misuse/use-case risk perspective"],
        "stability_windows": [("2021-01-01", "2021-12-31"), ("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31")],
    },
    "robotics": {
        "query": "https://github.com/ros-navigation/navigation2",
        "candidates": [
            "https://github.com/ros2/ros2",
            "https://github.com/ArduPilot/ardupilot",
            "https://github.com/PX4/PX4-Autopilot",
            "https://github.com/pallets/flask",
            "https://github.com/django/django",
            "https://github.com/expressjs/express",
        ],
        "expected_high_similarity": ["ros2", "ardupilot", "px4"],
        "controls": ["flask", "django", "express"],
        "profile": {
            "O1": 1, "O2": "11011", "O3": 5, "O4": 6, "O5": 7,
            "operational_environment": "land",
            "application_purpose": ["robotics", "planning", "integration"],
            "ml_algorithms": ["reinforcement", "clustering"],
            "dev_techniques": {"languages": ["cpp", "python"], "process": "agile"},
        },
        "justification": "Autonomous/semiautonomous robotics carries high operational and safety constraints.",
        "source_refs": ["CAIS taxonomy operational environment", "NIST CSWP 31 operational characteristics"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "aerial_autonomy": {
        "query": "https://github.com/PX4/PX4-Autopilot",
        "candidates": [
            "https://github.com/ArduPilot/ardupilot",
            "https://github.com/autowarefoundation/autoware",
            "https://github.com/facebook/react",
            "https://github.com/django/django",
            "https://github.com/pallets/flask",
        ],
        "expected_high_similarity": ["ardupilot", "autoware"],
        "controls": ["react", "django", "flask"],
        "profile": {
            "O1": 1, "O2": "11110", "O3": 7, "O4": 7, "O5": 9,
            "operational_environment": "air",
            "application_purpose": ["robotics", "planning", "perception", "vehicles"],
            "ml_algorithms": ["deep_learning", "reinforcement"],
            "dev_techniques": {"languages": ["cpp", "python", "c"], "process": "agile"},
        },
        "justification": "Aerial autonomy is real-time and safety-critical with high mission reliability demands.",
        "source_refs": ["CAIS taxonomy environment/purpose", "NIST CSWP 31 criticality emphasis"],
        "stability_windows": [("2021-01-01", "2021-12-31"), ("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31")],
    },
    "financial_risk": {
        "query": "https://github.com/scikit-learn/scikit-learn",
        "candidates": [
            "https://github.com/microsoft/LightGBM",
            "https://github.com/dmlc/xgboost",
            "https://github.com/facebook/react",
            "https://github.com/django/django",
            "https://github.com/expressjs/express",
        ],
        "expected_high_similarity": ["lightgbm", "xgboost"],
        "controls": ["react", "django", "express"],
        "profile": {
            "O1": 0, "O2": "10011", "O3": 7, "O4": 6, "O5": 2,
            "operational_environment": "cyber",
            "application_purpose": ["reasoning", "learning", "risk"],
            "ml_algorithms": ["deep_learning", "regression", "classification"],
            "dev_techniques": {"languages": ["python", "cpp"], "process": "agile"},
        },
        "justification": "Financial/credit risk ML is high-stakes (EU high-risk), material impact, typically assistive.",
        "source_refs": ["CAIS taxonomy application purpose", "NIST CSWP 31 high-risk use cases"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31")],
    },
    # --- New CAIS-aligned domains ---
    "industrial_robotics": {
        "query": "https://github.com/ros-controls/ros2_control",
        "candidates": [
            "https://github.com/ros-planning/moveit2",
            "https://github.com/ros-controls/ros2_controllers",
            "https://github.com/cartographer-project/cartographer",
            "https://github.com/ros-industrial/industrial_core",
            "https://github.com/ros2/rclcpp",
            "https://github.com/django/django",
            "https://github.com/expressjs/express",
        ],
        "expected_high_similarity": ["moveit2", "ros2_controllers", "industrial_core"],
        "controls": ["django", "express"],
        "profile": {
            "O1": 1, "O2": "11011", "O3": 6, "O4": 5, "O5": 8,
            "operational_environment": "industrial",
            "application_purpose": ["robotics", "manufacturing", "manipulation", "control"],
            "ml_algorithms": ["reinforcement", "control"],
            "dev_techniques": {"languages": ["cpp", "python"], "process": "agile"},
        },
        "justification": "Industrial robot control stacks are safety-critical (factory floors, human-robot collaboration).",
        "source_refs": ["CAIS taxonomy operational environment", "NIST CSWP 31"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "recommender_systems": {
        "query": "https://github.com/microsoft/recommenders",
        "candidates": [
            "https://github.com/lenskit/lkpy",
            "https://github.com/RUCAIBox/RecBole",
            "https://github.com/NicolasHug/Surprise",
            "https://github.com/tensorflow/recommenders",
            "https://github.com/pytorch/torchrec",
            "https://github.com/django/django",
            "https://github.com/pallets/flask",
        ],
        "expected_high_similarity": ["lkpy", "recbole", "torchrec"],
        "controls": ["django", "flask"],
        "profile": {
            "O1": 0, "O2": "10010", "O3": 5, "O4": 8, "O5": 1,
            "operational_environment": "cyber",
            "application_purpose": ["recommendation", "ranking", "personalization"],
            "ml_algorithms": ["deep_learning", "collaborative_filtering"],
            "dev_techniques": {"languages": ["python"], "process": "agile"},
        },
        "justification": "Recommender/ranking systems have high social impact (content filtering, hiring, credit decisions).",
        "source_refs": ["CAIS taxonomy application purpose", "NIST public services"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "security_identity": {
        "query": "https://github.com/keycloak/keycloak",
        "candidates": [
            "https://github.com/ory/hydra",
            "https://github.com/authelia/authelia",
            "https://github.com/casdoor/casdoor",
            "https://github.com/zitadel/zitadel",
            "https://github.com/dexidp/dex",
            "https://github.com/django/django",
            "https://github.com/facebook/react",
        ],
        "expected_high_similarity": ["hydra", "authelia", "zitadel"],
        "controls": ["django", "react"],
        "profile": {
            "O1": 0, "O2": "10011", "O3": 8, "O4": 7, "O5": 2,
            "operational_environment": "cyber",
            "application_purpose": ["authentication", "authorization", "identity"],
            "ml_algorithms": ["none"],
            "dev_techniques": {"languages": ["java", "go"], "process": "agile"},
        },
        "justification": "IAM systems are critical infrastructure; breaches have severe financial and social consequences.",
        "source_refs": ["CAIS taxonomy operational characteristics", "NIST CSWP 31"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "content_moderation": {
        "query": "https://github.com/unitaryai/detoxify",
        "candidates": [
            "https://github.com/facebookresearch/fasttext",
            "https://github.com/huggingface/setfit",
            "https://github.com/cardiffnlp/tweeteval",
            "https://github.com/django/django",
            "https://github.com/expressjs/express",
        ],
        "expected_high_similarity": ["fasttext", "tweeteval", "setfit"],
        "controls": ["django", "express"],
        "profile": {
            "O1": 0, "O2": "10010", "O3": 3, "O4": 9, "O5": 2,
            "operational_environment": "cyber",
            "application_purpose": ["classification", "content_filtering", "moderation"],
            "ml_algorithms": ["deep_learning", "nlp"],
            "dev_techniques": {"languages": ["python"], "process": "agile"},
        },
        "justification": "Content moderation AI has extreme societal impact (O4=9); errors cause real-world harm.",
        "source_refs": ["CAIS taxonomy application purpose", "NIST public services"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "public_sector_fairness": {
        "query": "https://github.com/fairlearn/fairlearn",
        "candidates": [
            "https://github.com/Trusted-AI/AIF360",
            "https://github.com/dssg/aequitas",
            "https://github.com/microsoft/responsible-ai-toolbox",
            "https://github.com/cosmicBboy/themis-ml",
            "https://github.com/django/django",
            "https://github.com/pallets/flask",
        ],
        "expected_high_similarity": ["aif360", "aequitas", "responsible-ai-toolbox"],
        "controls": ["django", "flask"],
        "profile": {
            "O1": 0, "O2": "10011", "O3": 7, "O4": 8, "O5": 3,
            "operational_environment": "cyber",
            "application_purpose": ["fairness", "auditing", "risk_scoring"],
            "ml_algorithms": ["classification", "regression"],
            "dev_techniques": {"languages": ["python"], "process": "agile"},
        },
        "justification": "Public-sector risk scoring (credit, benefits, hiring) directly referenced in paper as biased risk scores and Medicaid appeals.",
        "source_refs": ["CAIS taxonomy application purpose", "Paper: biased risk scores, Medicaid appeals"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
    "cybersecurity_threat_detection": {
        "query": "https://github.com/MISP/MISP",
        "candidates": [
            "https://github.com/wazuh/wazuh",
            "https://github.com/elastic/detection-rules",
            "https://github.com/crowdsecurity/crowdsec",
            "https://github.com/ossec/ossec-hids",
            "https://github.com/django/django",
            "https://github.com/facebook/react",
        ],
        "expected_high_similarity": ["wazuh", "detection-rules", "crowdsec"],
        "controls": ["django", "react"],
        "profile": {
            "O1": 0, "O2": "10011", "O3": 8, "O4": 7, "O5": 3,
            "operational_environment": "cyber",
            "application_purpose": ["threat_detection", "monitoring", "intrusion_detection"],
            "ml_algorithms": ["anomaly_detection", "rule_based"],
            "dev_techniques": {"languages": ["python", "php"], "process": "agile"},
        },
        "justification": "Cybersecurity threat intel and IDS are defense-critical with high financial and societal impact.",
        "source_refs": ["CAIS taxonomy operational characteristics", "NIST CSWP 31"],
        "stability_windows": [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")],
    },
}

# --- notebook cell 119 (id=3b2ceeaf) ---
import requests, math, re
from typing import Dict, List, Tuple, Optional
from collections import Counter

_GH_API = "https://api.github.com"

def _gh_get(path: str, token: Optional[str] = None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"{_GH_API}{path}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def _repo_slug(url: str) -> str:
    return url.replace("https://github.com/", "").strip("/")


def _repo_languages(slug: str, token: Optional[str] = None) -> Dict[str, int]:
    try:
        return _gh_get(f"/repos/{slug}/languages", token)
    except Exception:
        return {}


def _repo_topics(slug: str, token: Optional[str] = None) -> List[str]:
    try:
        data = _gh_get(f"/repos/{slug}/topics", token)
        return data.get("names", [])
    except Exception:
        return []


def _repo_readme_text(slug: str, token: Optional[str] = None) -> str:
    try:
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(f"{_GH_API}/repos/{slug}/readme", headers=headers, timeout=30)
        if r.status_code == 200:
            return r.text[:8000]
    except Exception:
        pass
    return ""


def _repo_tree_paths(slug: str, token: Optional[str] = None, limit: int = 300) -> List[str]:
    try:
        data = _gh_get(f"/repos/{slug}/git/trees/HEAD?recursive=1", token)
        return [t["path"] for t in data.get("tree", [])[:limit]]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Baseline 1: Code-Centric Similarity (token / structure overlap)
# ---------------------------------------------------------------------------
def code_clone_similarity(
    query: str,
    candidates: List[str],
    token: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """Approximate code-clone similarity via language mix + file-tree token overlap."""
    q_slug = _repo_slug(query)
    q_langs = _repo_languages(q_slug, token)
    q_topics = set(_repo_topics(q_slug, token))
    q_paths = _repo_tree_paths(q_slug, token)
    q_exts = Counter(p.rsplit(".", 1)[-1].lower() for p in q_paths if "." in p)
    q_dirs = Counter(p.split("/")[0].lower() for p in q_paths if "/" in p)

    results = []
    for c in candidates:
        c_slug = _repo_slug(c)
        c_langs = _repo_languages(c_slug, token)
        c_topics = set(_repo_topics(c_slug, token))
        c_paths = _repo_tree_paths(c_slug, token)
        c_exts = Counter(p.rsplit(".", 1)[-1].lower() for p in c_paths if "." in p)
        c_dirs = Counter(p.split("/")[0].lower() for p in c_paths if "/" in p)

        # Language distribution cosine
        all_langs = set(q_langs) | set(c_langs)
        if all_langs:
            a = [q_langs.get(l, 0) for l in all_langs]
            b = [c_langs.get(l, 0) for l in all_langs]
            lang_sim = cosine(a, b)
        else:
            lang_sim = 0.0

        # File-extension overlap (Jaccard)
        ext_keys = set(q_exts) | set(c_exts)
        ext_jaccard = len(set(q_exts) & set(c_exts)) / max(len(ext_keys), 1)

        # Directory-name overlap (Jaccard)
        dir_keys = set(q_dirs) | set(c_dirs)
        dir_jaccard = len(set(q_dirs) & set(c_dirs)) / max(len(dir_keys), 1)

        # Topic overlap (Jaccard)
        topic_jaccard = len(q_topics & c_topics) / max(len(q_topics | c_topics), 1)

        sim = 0.35 * lang_sim + 0.25 * ext_jaccard + 0.20 * dir_jaccard + 0.20 * topic_jaccard
        results.append((c, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Baseline 2: Dynamic / Behavioral Similarity
# ---------------------------------------------------------------------------
_TEST_FRAMEWORKS = re.compile(
    r"\b(pytest|unittest|jest|mocha|junit|gtest|catch2|rspec|minitest|"
    r"nose2|tox|ci|travis|github.actions|circleci|jenkins)\b", re.I
)
_BUG_LABELS = re.compile(r"\b(bug|fix|crash|error|fail|regression|security)\b", re.I)


def dynamic_behavior_similarity(
    query: str,
    candidates: List[str],
    token: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """Approximate behavioral similarity from CI signals, test-framework mentions, and issue labels."""
    def _signals(slug):
        readme = _repo_readme_text(slug, token).lower()
        paths = _repo_tree_paths(slug, token)
        path_text = " ".join(paths).lower()
        test_hits = set(_TEST_FRAMEWORKS.findall(readme + " " + path_text))
        has_ci = any(k in path_text for k in [".github/workflows", ".travis", "jenkinsfile", ".circleci"])
        try:
            issues = _gh_get(f"/repos/{slug}/issues?state=all&per_page=50&labels=bug", token)
            bug_count = len(issues) if isinstance(issues, list) else 0
        except Exception:
            bug_count = 0
        return {"test_frameworks": test_hits, "has_ci": has_ci, "bug_issues": bug_count}

    q_sig = _signals(_repo_slug(query))
    results = []
    for c in candidates:
        c_sig = _signals(_repo_slug(c))
        # Test-framework Jaccard
        all_tests = q_sig["test_frameworks"] | c_sig["test_frameworks"]
        tf_jaccard = len(q_sig["test_frameworks"] & c_sig["test_frameworks"]) / max(len(all_tests), 1)
        # CI match
        ci_match = 1.0 if q_sig["has_ci"] == c_sig["has_ci"] else 0.0
        # Bug-issue ratio similarity
        max_bugs = max(q_sig["bug_issues"], c_sig["bug_issues"], 1)
        bug_sim = 1.0 - abs(q_sig["bug_issues"] - c_sig["bug_issues"]) / max_bugs
        sim = 0.50 * tf_jaccard + 0.25 * ci_match + 0.25 * bug_sim
        results.append((c, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Baseline 3: Deep / Cross-Language Similarity (README + tree embeddings)
# ---------------------------------------------------------------------------
def deep_code_similarity(
    query: str,
    candidates: List[str],
    token: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """Cross-language similarity via sentence-transformer embeddings of README + file tree."""
    global _deep_code_similarity_warned
    try:
        _deep_code_similarity_warned
    except NameError:
        _deep_code_similarity_warned = False
    encoder = _get_sentence_encoder()
    if not encoder:
        if not _deep_code_similarity_warned:
            print("[deep_code_similarity] sentence-transformers not available; returning empty. Install with: pip install sentence-transformers")
            _deep_code_similarity_warned = True
        return [(c, 0.0) for c in candidates]

    def _text(slug):
        readme = _repo_readme_text(slug, token)
        paths = _repo_tree_paths(slug, token, limit=200)
        tree_str = " ".join(p.replace("/", " ") for p in paths[:100])
        topics = " ".join(_repo_topics(slug, token))
        return f"{topics} {readme[:3000]} {tree_str}"

    q_text = _text(_repo_slug(query))
    all_texts = [q_text] + [_text(_repo_slug(c)) for c in candidates]

    embeddings = encoder.encode(all_texts, normalize_embeddings=True, show_progress_bar=False)
    q_emb = embeddings[0].tolist()

    results = []
    for c, emb in zip(candidates, embeddings[1:]):
        sim = cosine(q_emb, emb.tolist())
        results.append((c, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results

# --- notebook cell 126 (id=eb019bf3) ---
# =============================================================================
# Known Mirror Benchmark (metadata vs code-dependent baselines)
# =============================================================================
# Goal : show known source-code pairs are identified
# by our metadata approach at least as accurately as traditional code-dependent
# approaches (code-centric, dynamic/behavioral, cross-language).
#
# Design:
#   query      = upstream_url   (the canonical source)
#   true_match = mirror_url     (the known mirror)
#   candidates = [mirror_url] + negatives   (shuffled alphabetically)
#   Ground truth: upstream and mirror share the same commit SHA at a given ref,
#                 OR both are reachable and the pair is documented as official.
# =============================================================================

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json, random, itertools
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# ─── Test Pairs ───────────────────────────────────────────────────────────────
# 5 pairs from NextCompareReqs.pdf + 3 additional well-documented mirrors.
# Negatives are chosen to be from the same DOMAIN but clearly different projects.

KNOWN_MIRROR_PAIRS: List[Dict[str, object]] = [
    # --- PDF-required pairs (non-GitHub upstreams, resolved via git ls-remote) ---
    {
        "name": "V8",
        "upstream_url": "https://chromium.googlesource.com/v8/v8.git",
        "mirror_url": "https://github.com/v8/v8",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "GitHub states 'official mirror of the V8 Git repository'.",
        "negatives": [
            "https://github.com/nicmcd/libprim",
            "https://github.com/nicmcd/libfactory",
            "https://github.com/nicmcd/ratesim",
        ],
    },
    {
        "name": "Blender",
        "upstream_url": "https://projects.blender.org/blender/blender.git",
        "mirror_url": "https://github.com/blender/blender",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "Blender dev docs point to GitHub as the official mirror.",
        "negatives": [
            "https://github.com/godotengine/godot",
            "https://github.com/openscad/openscad",
            "https://github.com/mitsuba-renderer/mitsuba3",
        ],
    },
    {
        "name": "LibreOffice",
        "upstream_url": "https://git.libreoffice.org/core",
        "mirror_url": "https://github.com/LibreOffice/core",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "GitHub repo is read-only mirror; contributors use Gerrit upstream.",
        "negatives": [
            "https://github.com/apache/openoffice",
            "https://github.com/ONLYOFFICE/DocumentServer",
            "https://github.com/AbiWord/abiword",
        ],
    },
    {
        "name": "libapps",
        "upstream_url": "https://chromium.googlesource.com/apps/libapps",
        "mirror_url": "https://github.com/libapps/libapps-mirror",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "Upstream Chromium page explicitly documents the GitHub mirror.",
        "negatives": [
            "https://github.com/tmux/tmux",
            "https://github.com/tmux-plugins/tpm",
            "https://github.com/tmux-plugins/tmux-sensible",
        ],
    },
    {
        "name": "FreeType",
        "upstream_url": "https://gitlab.freedesktop.org/freetype/freetype.git",
        "mirror_url": "https://github.com/freetype/freetype",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "GitHub identifies itself as official mirror of upstream GitLab project.",
        "negatives": [
            "https://github.com/harfbuzz/harfbuzz",
            "https://github.com/fontforge/fontforge",
            "https://github.com/google/skia",
        ],
    },
    # --- Additional well-documented mirror pairs ---
    {
        "name": "Git",
        "upstream_url": "https://git.kernel.org/pub/scm/git/git.git",
        "mirror_url": "https://github.com/git/git",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "GitHub description: 'Git Source Code Mirror'. Canonical is kernel.org.",
        "negatives": [
            "https://github.com/libgit2/libgit2",
            "https://github.com/go-git/go-git",
            "https://github.com/isomorphic-git/isomorphic-git",
        ],
    },
    {
        "name": "GCC",
        "upstream_url": "https://gcc.gnu.org/git/gcc.git",
        "mirror_url": "https://github.com/gcc-mirror/gcc",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "GitHub org is literally named 'gcc-mirror'. Upstream is gcc.gnu.org.",
        "negatives": [
            "https://github.com/llvm/llvm-project",
            "https://github.com/rust-lang/rust",
            "https://github.com/AcademySoftwareFoundation/openvdb",
        ],
    },
    {
        "name": "FFmpeg",
        "upstream_url": "https://git.ffmpeg.org/ffmpeg.git",
        "mirror_url": "https://github.com/FFmpeg/FFmpeg",
        "alignment_ref": "HEAD",
        "official_mirror_claim": True,
        "notes": "GitHub description: 'Mirror of https://git.ffmpeg.org/ffmpeg.git'.",
        "negatives": [
            "https://github.com/GStreamer/gstreamer",
            "https://github.com/mltframework/mlt",
            "https://github.com/HandBrake/HandBrake",
        ],
    },
]

BENCHMARK_RESULTS_DIR = Path("results_benchmark")
BENCHMARK_RESULTS_DIR.mkdir(exist_ok=True)


def _github_slug_from_url(url: str) -> Optional[str]:
    s = (url or "").strip()
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)", s)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2).removesuffix('.git')}"


def _resolve_ref_via_ls_remote(url: str, ref: str = "HEAD") -> Optional[str]:
    """Resolve any git ref to a commit SHA using `git ls-remote`."""
    ref = (ref or "HEAD").strip()
    try:
        out = subprocess.check_output(
            ["git", "ls-remote", url, ref],
            text=True, timeout=30, stderr=subprocess.DEVNULL,
        ).strip()
        if not out:
            out = subprocess.check_output(
                ["git", "ls-remote", url, f"refs/tags/{ref}"],
                text=True, timeout=30, stderr=subprocess.DEVNULL,
            ).strip()
        if out:
            return out.split()[0]
    except Exception:
        pass
    return None

# --- notebook cell 148 (id=8f09e6c0) ---
# NOTE: `_infer_domain_key_from_url` / `_get_domain_hard_negatives` are **redefined** in patch cell `893d6fab`.
# Keep this cell for defaults / `build_argument_table`; run the patch cell so GitHub-topic-aware overrides apply.

DEFAULT_METADATA_HARD_NEGATIVES = [
    "https://github.com/django/django",
    "https://github.com/facebook/react",
    "https://github.com/tensorflow/tensorflow",
    "https://github.com/vim/vim",
]

DOMAIN_HARD_NEGATIVE_POOLS = {
    "ml": [
        "https://github.com/keras-team/keras",
        "https://github.com/dmlc/xgboost",
        "https://github.com/apache/spark",
        "https://github.com/scikit-learn/scikit-learn",
    ],
    "infra": [
        "https://github.com/kubernetes/kubernetes",
        "https://github.com/ansible/ansible",
        "https://github.com/prometheus/prometheus",
        "https://github.com/elastic/elasticsearch",
    ],
    "app": [
        "https://github.com/facebook/react",
        "https://github.com/django/django",
        "https://github.com/electron/electron",
        "https://github.com/Homebrew/brew",
    ],
    "systems": [
        "https://github.com/golang/go",
        "https://github.com/vim/vim",
        "https://github.com/bitcoin/bitcoin",
        "https://github.com/tensorflow/tensorflow",
    ],
}

DOMAIN_KEYWORDS = {
    "ml": ["tensorflow", "pytorch", "scikit", "xgboost", "monai", "keras", "llm", "langchain", "vllm"],
    "infra": ["kubernetes", "prometheus", "ansible", "elastic", "docker", "terraform"],
    "app": ["react", "django", "electron", "next", "frontend", "web"],
    "systems": ["golang", "linux", "compiler", "kernel", "vim", "bitcoin"],
}


def _infer_domain_key_from_url(repo_url: str) -> str:
    slug = (_repo_slug(repo_url) or "").lower()
    for domain, kws in DOMAIN_KEYWORDS.items():
        if any(kw in slug for kw in kws):
            return domain
    return "app"


def _get_domain_hard_negatives(query_url: str, target_url: str, limit: int = REDUX3_DOMAIN_NEGATIVE_LIMIT) -> List[str]:
    qd = _infer_domain_key_from_url(query_url)
    td = _infer_domain_key_from_url(target_url)
    pool: List[str] = []
    for k in [qd, td, "ml", "infra", "app", "systems"]:
        pool.extend(DOMAIN_HARD_NEGATIVE_POOLS.get(k, []))
    pool.extend(DEFAULT_METADATA_HARD_NEGATIVES)
    pool = _filter_metadata_pool_urls(query_url, target_url, pool)
    return list(dict.fromkeys(pool))[:max(1, int(limit))]

TEST3_METADATA_HARD_NEGATIVES = [
    "https://github.com/django/django",
    "https://github.com/facebook/react",
    "https://github.com/tensorflow/tensorflow",
    "https://github.com/vim/vim",
    "https://github.com/keras-team/keras",
    "https://github.com/elastic/elasticsearch",
    "https://github.com/prometheus/prometheus",
    "https://github.com/bitcoin/bitcoin",
    "https://github.com/Homebrew/brew",
    "https://github.com/golang/go",
    "https://github.com/ansible/ansible",
    "https://github.com/apache/spark",
]


def build_argument_table(
    pair_defs: List[Tuple[str, str, str]],
    known_similarity_pct: float,
    token: Optional[str] = None,
    max_commits: int = 150,
    metadata_windows: Optional[List[int]] = None,
    metadata_window_weights: Optional[Dict[int, float]] = None,
    metadata_weights: Optional[str] = None,
    metadata_extra_candidates: Optional[List[str]] = None,
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    normalization_mode: str = "global_minmax",
    pairwise_scoring: bool = True,
    include_alt_metadata: bool = False,
    reporting_mode: str = REDUX3_DEFAULT_REPORTING_RETRIEVAL,
    coverage_penalty_lambda: float = REDUX3_COVERAGE_PENALTY_LAMBDA,
    use_domain_hard_negatives: bool = True,
) -> pd.DataFrame:
    """Build a table: Test, Known similarity, Metadata, Code centric, Dynamic, Cross language.

    REDUX_3 defaults favor strict discrimination with contrastive reporting and domain-aware negatives.
    """
    rows = []
    for test_name, query_url, target_url in pair_defs:
        scores = _method_score_percent_for_target(
            query_url,
            target_url,
            token=token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or REDUX3_METADATA_WINDOWS,
            metadata_window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
            metadata_weights=metadata_weights,
            metadata_extra_candidates=metadata_extra_candidates,
            include_alt_metadata=include_alt_metadata,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
            coverage_penalty_lambda=coverage_penalty_lambda,
            use_domain_hard_negatives=use_domain_hard_negatives,
        )
        rows.append({
            "Test": test_name,
            "Known similarity": f"{known_similarity_pct:.0f}%",
            "Metadata": scores["Metadata"],
            "Code centric": scores["Code centric"],
            "Dynamic": scores["Dynamic"],
            "Cross language": scores["Cross language"],
            "Query": query_url,
            "Target": target_url,
        })
    return pd.DataFrame(rows)

# --- notebook cell 149 (id=0ca19290) ---
import re
import shutil


def _canonical_github_repo_url(s: str) -> str:
    raw = str(s).strip()
    if not raw:
        raise ValueError("empty repo specifier")
    if raw.lower().startswith(("https://github.com/", "http://github.com/")):
        m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", raw.rstrip("/"), re.I)
        if not m:
            raise ValueError(f"not a valid GitHub repo URL: {raw!r}")
        name = m.group(2).removesuffix(".git")
        return f"https://github.com/{m.group(1)}/{name}"
    if "/" in raw:
        owner, name = raw.split("/", 1)
        name = name.removesuffix(".git").strip("/")
        return f"https://github.com/{owner.strip('/')}/{name}"
    raise ValueError(f"expected owner/repo or github.com URL, got: {raw!r}")


def _load_custom_pairs(path: str = "30_Pairs.json") -> List[Dict[str, object]]:
    with Path(path).open(encoding="utf-8-sig") as f:
        payload = json.load(f)
    pairs = payload["pairs"] if isinstance(payload, dict) and "pairs" in payload else payload
    assert len(pairs) == 30, f"expected 30 pairs, got {len(pairs)}"
    return pairs


def _collect_pair_repo_urls(pairs: List[Dict[str, object]]) -> List[str]:
    urls = []
    for p in pairs:
        ra = str(p.get("RepoA", "")).strip()
        rb = str(p.get("RepoB", "")).strip()
        if ra:
            urls.append(_canonical_github_repo_url(ra))
        if rb:
            urls.append(_canonical_github_repo_url(rb))
    return sorted(set(urls))


def fit_global_minmax_for_all_benchmark_tables(
    pairs_path: str = "30_Pairs.json",
    max_commits: int = 150,
    strategy: str = "minmax",
) -> None:
    """Fit one global normalizer over 30-pair repos plus control pairs.

    ``strategy`` may be ``"minmax"``, ``"minmax_winsor"`` (see ``MinMaxNormalizerWinsor``), or ``"zscore"``.
    """
    clear_global_normalizers()
    urls = set(_collect_pair_repo_urls(_load_custom_pairs(pairs_path)))
    for p in KNOWN_MIRROR_PAIRS:
        urls.add(_canonical_github_repo_url(str(p["mirror_url"])))

    functional = [
        ("https://github.com/tensorflow/tensorflow", "https://github.com/pytorch/pytorch"),
        ("https://github.com/microsoft/vscode", "https://github.com/electron/electron"),
        ("https://github.com/commaai/openpilot", "https://github.com/autowarefoundation/autoware"),
        ("https://github.com/Project-MONAI/MONAI", "https://github.com/tensorflow/tensorflow"),
    ]
    dissimilar = [
        ("https://github.com/tensorflow/tensorflow", "https://github.com/django/django"),
        ("https://github.com/microsoft/vscode", "https://github.com/dmlc/xgboost"),
        ("https://github.com/commaai/openpilot", "https://github.com/scikit-learn/scikit-learn"),
        ("https://github.com/Project-MONAI/MONAI", "https://github.com/electron/electron"),
    ]
    for qu, tu in functional + dissimilar:
        urls.add(_canonical_github_repo_url(qu))
        urls.add(_canonical_github_repo_url(tu))

    fit_global_normalizer(
        sorted(urls),
        metrics=CAIS_METRICS,
        token=github_token,
        max_commits=max_commits,
        strategy=strategy,
    )
    print(f"Global min-max normalizer fit on {len(urls)} unique repos.")

# --- notebook cell 150 (id=893d6fab) ---
# === Reliability + Discrimination Patch Overrides (research-safe defaults) ===

import math
import requests
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

# Lightweight diagnostics (used by benchmark/reporting)
BASELINE_COVERAGE: Dict[str, Dict[str, float]] = {}
API_FAIL_COUNT = 0

# Tunable contrastive sigmoid slope (must match `_contrastive_adjust`).
REDUX3_CONTRASTIVE_TEMPERATURE = 6.0


def _gh_get(path: str, token: Optional[str] = None, retries: int = 2, backoff: float = 1.5) -> dict:
    """GitHub GET with small retry/backoff and explicit failures."""
    global API_FAIL_COUNT
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{_GH_API}{path}", headers=headers, timeout=30)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff ** attempt)
            else:
                API_FAIL_COUNT += 1
    raise last_err


def _repo_tree_paths(slug: str, token: Optional[str] = None, limit: int = 300) -> List[str]:
    """Resolve default branch -> commit tree SHA -> recursive tree paths."""
    try:
        repo = _gh_get(f"/repos/{slug}", token)
        default_branch = repo.get("default_branch", "main")
        commit = _gh_get(f"/repos/{slug}/commits/{default_branch}", token)
        tree_sha = commit.get("commit", {}).get("tree", {}).get("sha")
        if not tree_sha:
            return []
        data = _gh_get(f"/repos/{slug}/git/trees/{tree_sha}?recursive=1", token)
        return [t.get("path", "") for t in data.get("tree", [])[:limit] if t.get("path")]
    except Exception:
        return []


def code_clone_similarity(
    query: str,
    candidates: List[str],
    token: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """Code-centric similarity with coverage-aware component renormalization."""
    q_slug = _repo_slug(query)
    q_langs = _repo_languages(q_slug, token)
    q_topics = set(_repo_topics(q_slug, token))
    q_paths = _repo_tree_paths(q_slug, token)
    q_exts = Counter(p.rsplit(".", 1)[-1].lower() for p in q_paths if "." in p)
    q_dirs = Counter(p.split("/")[0].lower() for p in q_paths if "/" in p)

    results = []
    for c in candidates:
        c_slug = _repo_slug(c)
        c_langs = _repo_languages(c_slug, token)
        c_topics = set(_repo_topics(c_slug, token))
        c_paths = _repo_tree_paths(c_slug, token)
        c_exts = Counter(p.rsplit(".", 1)[-1].lower() for p in c_paths if "." in p)
        c_dirs = Counter(p.split("/")[0].lower() for p in c_paths if "/" in p)

        comps = {}
        weights = {}

        all_langs = set(q_langs) | set(c_langs)
        if all_langs:
            a = [q_langs.get(l, 0) for l in all_langs]
            b = [c_langs.get(l, 0) for l in all_langs]
            comps["lang"] = cosine(a, b)
            weights["lang"] = 0.35

        ext_keys = set(q_exts) | set(c_exts)
        if ext_keys:
            comps["ext"] = len(set(q_exts) & set(c_exts)) / max(len(ext_keys), 1)
            weights["ext"] = 0.25

        dir_keys = set(q_dirs) | set(c_dirs)
        if dir_keys:
            comps["dir"] = len(set(q_dirs) & set(c_dirs)) / max(len(dir_keys), 1)
            weights["dir"] = 0.20

        topic_keys = q_topics | c_topics
        if topic_keys:
            comps["topic"] = len(q_topics & c_topics) / max(len(topic_keys), 1)
            weights["topic"] = 0.20

        total_w = sum(weights.values())
        if total_w <= 0:
            sim = 0.0
            coverage = 0.0
        else:
            sim = sum(weights[k] * comps[k] for k in comps) / total_w
            coverage = total_w / (0.35 + 0.25 + 0.20 + 0.20)

        BASELINE_COVERAGE[c] = BASELINE_COVERAGE.get(c, {})
        BASELINE_COVERAGE[c]["cc_coverage"] = float(round(coverage, 4))
        results.append((c, float(sim)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def dynamic_behavior_similarity(
    query: str,
    candidates: List[str],
    token: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """Behavioral similarity with reduced 0.50 fallback bias and coverage tracking."""

    def _signals(slug):
        readme = _repo_readme_text(slug, token).lower()
        paths = _repo_tree_paths(slug, token)
        path_text = " ".join(paths).lower()
        test_hits = set(_TEST_FRAMEWORKS.findall(readme + " " + path_text))
        has_ci = any(k in path_text for k in [".github/workflows", ".travis", "jenkinsfile", ".circleci"])
        bug_missing = False
        try:
            issues = _gh_get(f"/repos/{slug}/issues?state=all&per_page=50&labels=bug", token)
            bug_count = len(issues) if isinstance(issues, list) else 0
        except Exception:
            bug_count = 0
            bug_missing = True
        return {
            "test_frameworks": test_hits,
            "has_ci": has_ci,
            "bug_issues": bug_count,
            "paths_present": bool(paths),
            "bug_missing": bug_missing,
        }

    q_sig = _signals(_repo_slug(query))
    results = []
    for c in candidates:
        c_sig = _signals(_repo_slug(c))

        all_tests = q_sig["test_frameworks"] | c_sig["test_frameworks"]
        tf_jaccard = len(q_sig["test_frameworks"] & c_sig["test_frameworks"]) / max(len(all_tests), 1)

        # if neither side has path evidence, ci contributes neutral (0.5) not perfect match (1.0)
        if (not q_sig["paths_present"]) and (not c_sig["paths_present"]):
            ci_score = 0.5
        else:
            ci_score = 1.0 if q_sig["has_ci"] == c_sig["has_ci"] else 0.0

        # if both bug data unavailable/zero, keep neutral instead of perfect
        if (q_sig["bug_missing"] and c_sig["bug_missing"]) or (q_sig["bug_issues"] == 0 and c_sig["bug_issues"] == 0):
            bug_sim = 0.5
        else:
            max_bugs = max(q_sig["bug_issues"], c_sig["bug_issues"], 1)
            bug_sim = 1.0 - abs(q_sig["bug_issues"] - c_sig["bug_issues"]) / max_bugs

        # higher emphasis on framework overlap, less on binary indicators
        sim = 0.70 * tf_jaccard + 0.15 * ci_score + 0.15 * bug_sim

        coverage = 0.0
        coverage += 0.50 if len(all_tests) > 0 else 0.0
        coverage += 0.25 if (q_sig["paths_present"] or c_sig["paths_present"]) else 0.0
        coverage += 0.25 if not (q_sig["bug_missing"] and c_sig["bug_missing"]) else 0.0

        BASELINE_COVERAGE[c] = BASELINE_COVERAGE.get(c, {})
        BASELINE_COVERAGE[c]["dyn_coverage"] = float(round(coverage, 4))

        results.append((c, float(sim)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _family_cosine_score(
    q_vec: Dict[str, float],
    c_vec: Dict[str, float],
    feature_keys: List[str],
    fam_weights: Dict[str, float],
    family_score_norm: str = "raw_cosine",
    min_family_keys: int = 2,
    coverage_penalty_lambda: float = REDUX3_COVERAGE_PENALTY_LAMBDA,
) -> Tuple[float, Dict[str, float], Dict[str, bool]]:
    """Family-level scoring with explicit norm modes and coverage penalty."""
    raw_scores: Dict[str, float] = {}
    family_present: Dict[str, bool] = {}

    weighted_sum_raw = 0.0
    weight_total = 0.0
    covered_weight = 0.0

    for fam, _prefixes in FAMILY_FEATURE_PREFIXES.items():
        fam_keys = _keys_for_family(feature_keys, fam)
        present = len(fam_keys) >= min_family_keys
        family_present[fam] = present
        s = _safe_cosine_from_keys(q_vec, c_vec, fam_keys) if present else 0.0
        raw_scores[fam] = s

        w_key = FAMILY_TO_WEIGHT_KEY[fam]
        w = float(fam_weights.get(w_key, 1.0))
        if w <= 0:
            continue
        weight_total += w
        if present:
            covered_weight += w
            weighted_sum_raw += w * s

    if covered_weight <= 1e-12:
        return 0.0, raw_scores, family_present

    raw_combined = weighted_sum_raw / covered_weight

    if family_score_norm == "cosine_to_unit":
        combined = (raw_combined + 1.0) / 2.0
    elif family_score_norm == "raw_cosine":
        combined = raw_combined
    elif family_score_norm == "temperature":
        temp = 2.0
        combined = math.tanh(raw_combined / temp)
    else:
        raise ValueError(f"Unknown family_score_norm: {family_score_norm}")

    coverage_ratio = covered_weight / max(weight_total, 1e-12)
    penalized = combined - coverage_penalty_lambda * (1.0 - coverage_ratio)

    if family_score_norm == "raw_cosine":
        final_score = max(0.0, min(1.0, (penalized + 1.0) / 2.0))
    else:
        final_score = max(0.0, min(1.0, penalized))

    return final_score, raw_scores, family_present


def _contrastive_adjust(raw_score: float, neg_scores: List[float]) -> float:
    """Contrastive reporting score: compare against median hard-negative score."""
    if not neg_scores:
        return raw_score
    baseline = float(np.median(neg_scores))
    delta = raw_score - baseline
    return float(1.0 / (1.0 + np.exp(-float(REDUX3_CONTRASTIVE_TEMPERATURE) * delta)))


def _metadata_similarity(
    query: str,
    candidates: List[str],
    token: Optional[str] = None,
    max_commits: int = 150,
    windows: Optional[List[int]] = None,
    weights: Optional[str] = None,
    normalization_mode: str = "global_minmax",
    pairwise_scoring: bool = True,
    scoring_mode: str = "weighted_cosine",
    family_score_norm: str = "raw_cosine",
    coverage_penalty_lambda: float = REDUX3_COVERAGE_PENALTY_LAMBDA,
    window_weights: Optional[Dict[int, float]] = None,
    apply_post_pool_minmax: bool = True,
):
    token = token or github_token
    weights = weights or CAIS_WEIGHTS_STRICT
    windows = windows or REDUX3_METADATA_WINDOWS
    window_weights = window_weights or REDUX3_WINDOW_WEIGHTS

    score_accum = {c: [] for c in candidates}
    family_detail: Dict[str, Dict[str, float]] = {c: {} for c in candidates}

    for w in windows:
        cap = min(int(w), int(max_commits))
        if cap < 1:
            continue

        args = _build_compare_args(
            query=query,
            candidates=candidates,
            metrics=CAIS_METRICS,
            cais_profile_path=None,
            max_commits=cap,
            weights=weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
        )
        args.github_token = token

        if scoring_mode == "weighted_cosine":
            ranked = get_pairwise_similarity(args) if pairwise_scoring else get_ranked_similarity(args)
        elif scoring_mode == "family_cosine":
            metric_list = [m.strip() for m in CAIS_METRICS.split(",")]
            repos = [query] + candidates
            vecs: List[Dict[str, float]] = []
            for r in repos:
                try:
                    vec = compute_features_for_repo(
                        r,
                        metric_list,
                        since=None,
                        until=None,
                        github_token=token,
                        max_commits=cap,
                    )
                    vecs.append(vec)
                except Exception:
                    vecs.append({})

            if len(vecs) < 2 or not any(vecs):
                ranked = []
            else:
                norm = _get_normalizer_for_mode(normalization_mode, vecs)
                normed = [norm.transform(v) for v in vecs]
                common_keys = set(normed[0].keys())
                for v in normed[1:]:
                    common_keys &= v.keys()
                feature_keys = sorted(common_keys)
                fam_weights = parse_weights(weights)
                q_vec = normed[0]
                ranked = []
                for i, c in enumerate(candidates, start=1):
                    c_vec = normed[i]
                    s, raw_fam, _present = _family_cosine_score(
                        q_vec=q_vec,
                        c_vec=c_vec,
                        feature_keys=feature_keys,
                        fam_weights=fam_weights,
                        family_score_norm=family_score_norm,
                        coverage_penalty_lambda=coverage_penalty_lambda,
                    )
                    family_detail[c] = raw_fam
                    ranked.append((c, float(s)))
                ranked.sort(key=lambda x: x[1], reverse=True)
        else:
            raise ValueError(f"Unknown scoring_mode: {scoring_mode}")

        ranked = ranked or []
        ranked_dict = {repo: score for repo, score in ranked}
        wgt = float(window_weights.get(int(w), 1.0)) if isinstance(window_weights, dict) else 1.0
        for c in candidates:
            score_accum[c].append((ranked_dict.get(c, 0.0), wgt))

    averaged = []
    for c, vals in score_accum.items():
        if not vals:
            averaged.append((c, 0.0))
            continue
        num = sum(float(v) * float(w) for v, w in vals)
        den = sum(float(w) for _v, w in vals)
        averaged.append((c, float(num / den) if den > 1e-12 else 0.0))

    # Only min-max when there are multiple candidates AND meaningful spread.
    if apply_post_pool_minmax and normalization_mode == "global_minmax" and len(averaged) > 1:
        vals = [s for _, s in averaged]
        lo, hi = min(vals), max(vals)
        if hi > lo:
            averaged = [(c, (s - lo) / (hi - lo)) for c, s in averaged]

    # expose explainability payload for downstream reporting
    _metadata_similarity.last_family_detail = family_detail

    averaged.sort(key=lambda x: x[1], reverse=True)
    return averaged


# small defaults for stricter evaluation protocol
STRICT_ONLY = True


def validate_pair_alignment(pair: Dict[str, object], token: Optional[str] = None) -> Dict[str, object]:
    """
    Alignment guardrail using git ls-remote for any upstream host.
    Strict mode: both resolve to same SHA.
    Fallback: if both sides respond but HEAD differs (mirror lag),
    include with 'documentation_backed' status when official_mirror_claim is True.
    """
    ref = str(pair.get("alignment_ref", "HEAD"))
    upstream_url = str(pair.get("upstream_url", ""))
    mirror_url = str(pair.get("mirror_url", ""))
    official = bool(pair.get("official_mirror_claim", False))

    print(f"  [{pair.get('name')}] resolving mirror ref '{ref}'...")
    mirror_sha = _resolve_ref(mirror_url, ref, token=token)
    if not mirror_sha:
        return {
            "include": False,
            "status": "excluded_unresolved_mirror_ref",
            "reason": f"Mirror ref '{ref}' could not be resolved",
            "mirror_sha": None, "upstream_sha": None,
        }

    print(f"  [{pair.get('name')}] resolving upstream ref '{ref}'...")
    upstream_sha = _resolve_ref(upstream_url, ref, token=token)
    if not upstream_sha:
        return {
            "include": False,
            "status": "excluded_unresolved_upstream_ref",
            "reason": f"Upstream ref '{ref}' unresolvable via API and git ls-remote",
            "mirror_sha": mirror_sha, "upstream_sha": None,
        }

    if upstream_sha == mirror_sha:
        print(f"  [{pair.get('name')}] aligned: {upstream_sha[:12]}")
        return {
            "include": True,
            "status": "aligned_strict_sha_match",
            "reason": f"Exact SHA match at ref '{ref}'",
            "mirror_sha": mirror_sha, "upstream_sha": upstream_sha,
        }

    if official:
        print(f"  [{pair.get('name')}] SHA differs (mirror lag) but official_mirror_claim=True -> included")
        return {
            "include": True,
            "status": "aligned_documentation_backed",
            "reason": f"SHA mismatch (mirror lag) but official_mirror_claim=True; "
                      f"upstream={upstream_sha[:12]} mirror={mirror_sha[:12]}",
            "mirror_sha": mirror_sha, "upstream_sha": upstream_sha,
        }

    return {
        "include": False,
        "status": "excluded_ref_mismatch",
        "reason": f"SHA mismatch and no official_mirror_claim: "
                  f"upstream={upstream_sha[:12]} mirror={mirror_sha[:12]}",
        "mirror_sha": mirror_sha, "upstream_sha": upstream_sha,
    }


def _as_rank_dict(ranked: List[Tuple[str, float]]) -> Dict[str, Tuple[int, float]]:
    return {repo: (i + 1, score) for i, (repo, score) in enumerate(ranked)}



_REPO_STARS_CACHE: Dict[str, int] = {}
_REPO_TOPICS_CACHE: Dict[str, str] = {}


def _repo_stargazers_count(slug: str, token: Optional[str] = None) -> Optional[int]:
    if slug in _REPO_STARS_CACHE:
        return _REPO_STARS_CACHE[slug]
    try:
        data = _gh_get(f"/repos/{slug}", token)
        n = int(data.get("stargazers_count", 0) or 0)
        _REPO_STARS_CACHE[slug] = n
        return n
    except Exception:
        return None


def _repo_topics_blob(slug: str, token: Optional[str] = None) -> str:
    if slug in _REPO_TOPICS_CACHE:
        return _REPO_TOPICS_CACHE[slug]
    try:
        headers = {"Accept": "application/vnd.github.mercy-preview+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(f"{_GH_API}/repos/{slug}/topics", headers=headers, timeout=30)
        if r.status_code != 200:
            _REPO_TOPICS_CACHE[slug] = ""
            return ""
        names = (r.json() or {}).get("names") or []
        blob = " ".join(str(x).lower() for x in names if x)
        _REPO_TOPICS_CACHE[slug] = blob
        return blob
    except Exception:
        _REPO_TOPICS_CACHE[slug] = ""
        return ""


def _infer_domain_key_from_url(repo_url: str, token: Optional[str] = None) -> str:
    """Infer coarse domain bucket using slug heuristics + GitHub topics (when token allows)."""
    slug = (_repo_slug(repo_url) or "").lower()
    topics = _repo_topics_blob(slug, token)
    blob = slug + " " + topics
    for domain, kws in DOMAIN_KEYWORDS.items():
        if any(kw in blob for kw in kws):
            return domain
    return "app"


def _pick_star_matched_urls(
    pool: List[str],
    ref_slug: str,
    token: Optional[str] = None,
    ref_stars: Optional[int] = None,
    band_ratio: float = 0.35,
    max_checks: int = 16,
) -> List[str]:
    """Prefer URLs with stargazer counts within a band of ref_stars (cheap metadata-hard control)."""
    if ref_stars is None or ref_stars <= 0:
        return []
    lo = int(max(10, ref_stars * (1.0 - band_ratio)))
    hi = int(max(lo + 1, ref_stars * (1.0 + band_ratio)))
    out: List[str] = []
    for u in pool:
        if len(out) >= max_checks:
            break
        s = _repo_slug(u)
        if not s or s == ref_slug:
            continue
        sc = _repo_stargazers_count(s, token)
        if sc is None:
            continue
        if lo <= sc <= hi:
            out.append(u)
    return out


METADATA_NEAR_MISS_EXTRA = [
    "https://github.com/apache/spark",
    "https://github.com/pytorch/pytorch",
    "https://github.com/huggingface/transformers",
    "https://github.com/langchain-ai/langchain",
]


def _get_domain_hard_negatives(
    query_url: str,
    target_url: str,
    limit: int = REDUX3_DOMAIN_NEGATIVE_LIMIT,
    token: Optional[str] = None,
) -> List[str]:
    """Domain negatives + optional star-band near-misses + small curated near-miss list."""
    tok = token or github_token
    qd = _infer_domain_key_from_url(query_url, tok)
    td = _infer_domain_key_from_url(target_url, tok)
    pool: List[str] = []
    for k in [qd, td, "ml", "infra", "app", "systems"]:
        pool.extend(DOMAIN_HARD_NEGATIVE_POOLS.get(k, []))
    pool.extend(DEFAULT_METADATA_HARD_NEGATIVES)
    pool.extend(METADATA_NEAR_MISS_EXTRA)
    pool = _filter_metadata_pool_urls(query_url, target_url, pool)
    pool = list(dict.fromkeys(pool))

    ref_slug = (_repo_slug(target_url) or "").lower()
    ref_stars = _repo_stargazers_count(ref_slug, tok) if ref_slug else None
    near = _pick_star_matched_urls(pool, ref_slug, tok, ref_stars=ref_stars)
    merged = near + [u for u in pool if u not in near]
    return merged[: max(1, int(limit))]


def _metadata_similarity_contrastive_table_aligned(
    query: str,
    candidates: List[str],
    *,
    token: Optional[str],
    max_commits: int,
    windows: Optional[List[int]],
    window_weights: Optional[Dict[int, float]],
    weights: Optional[str],
    normalization_mode: str,
    pairwise_scoring: bool,
    family_score_norm: str,
    coverage_penalty_lambda: float,
) -> List[Tuple[str, float]]:
    """Match ``_method_score_percent_for_target(..., reporting_mode='contrastive')`` per candidate."""
    _ms = globals()["_metadata_similarity"]
    out: List[Tuple[str, float]] = []
    wins = windows or REDUX3_METADATA_WINDOWS
    wwg = window_weights or REDUX3_WINDOW_WEIGHTS
    for c in candidates:
        raw_rank = _ms(
            query,
            [c],
            token=token,
            max_commits=max_commits,
            windows=wins,
            weights=weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode="family_cosine",
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
            window_weights=wwg,
            apply_post_pool_minmax=False,
        )
        raw_c = float(raw_rank[0][1]) if raw_rank else 0.0
        hn = _get_domain_hard_negatives(query, c, token=token)
        neg_rank = _ms(
            query,
            hn,
            token=token,
            max_commits=max_commits,
            windows=wins,
            weights=weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode="family_cosine",
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
            window_weights=wwg,
            apply_post_pool_minmax=True,
        )
        neg_scores = [float(s) for _, s in (neg_rank or [])]
        adj = _contrastive_adjust(raw_c, neg_scores)
        out.append((c, float(adj)))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _metadata_similarity_rankpct_pool(
    query: str,
    candidates: List[str],
    *,
    token: Optional[str],
    max_commits: int,
    windows: Optional[List[int]],
    window_weights: Optional[Dict[int, float]],
    weights: Optional[str],
    normalization_mode: str,
    pairwise_scoring: bool,
    family_score_norm: str,
    coverage_penalty_lambda: float,
) -> List[Tuple[str, float]]:
    """Map raw pool scores to rank-fraction in [0,1] (same ordering as ``_metadata_rank_pct_display``)."""
    _ms = globals()["_metadata_similarity"]
    ranked = _ms(
        query,
        candidates,
        token=token,
        max_commits=max_commits,
        windows=windows or REDUX3_METADATA_WINDOWS,
        weights=weights,
        normalization_mode=normalization_mode,
        pairwise_scoring=pairwise_scoring,
        scoring_mode="family_cosine",
        family_score_norm=family_score_norm,
        coverage_penalty_lambda=coverage_penalty_lambda,
        window_weights=window_weights or REDUX3_WINDOW_WEIGHTS,
        apply_post_pool_minmax=True,
    )
    ranked = sorted(ranked or [], key=lambda x: x[1], reverse=True)
    urls = [u for u, _ in ranked]
    n = len(urls)
    if n <= 1:
        s0 = float(ranked[0][1]) if ranked else 0.0
        return [(urls[0], max(0.0, min(1.0, s0)))] if urls else []
    out = []
    for idx, u in enumerate(urls):
        frac = float(1.0 - idx / (n - 1))
        out.append((u, frac))
    return out



def _filter_metadata_pool_urls(query_url: str, target_url: str, urls: List[str]) -> List[str]:
    """Drop hard-negative URLs that duplicate query or target GitHub slugs (avoids pool distortion)."""
    q = (_repo_slug(query_url) or "").lower()
    t = (_repo_slug(target_url) or "").lower()
    out: List[str] = []
    for u in urls:
        s = (_repo_slug(u) or "").lower()
        if s and s in (q, t):
            continue
        out.append(u)
    return out


def _metadata_rank_pct_display(
    ranked: List[Tuple[str, float]],
    target_url: str,
) -> float:
    """Map target's rank in descending similarity to a 0–100 display score (best rank => 100)."""
    if not ranked:
        return 0.0
    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)
    urls = [u for u, _ in ranked]
    if target_url not in urls:
        return 0.0
    idx = urls.index(target_url)
    n = len(urls)
    if n <= 1:
        return float(round(max(0.0, min(1.0, ranked[0][1])) * 100.0, 2))
    return float(round(100.0 * (1.0 - idx / (n - 1)), 2))


def run_known_pair_benchmark(
    pairs: Optional[List[Dict[str, object]]] = None,
    token: Optional[str] = None,
    max_commits: int = 150,
    save_prefix: str = "known_mirror_benchmark",
    make_plots: bool = True,
    strict_only: bool = True,
    metadata_reporting_mode: str = REDUX3_DEFAULT_REPORTING_BENCHMARK,
    coverage_penalty_lambda: Optional[float] = None,
) -> Dict[str, object]:
    """Override runner with strict/sensitivity split control."""
    token = token or github_token
    pairs = pairs or KNOWN_MIRROR_PAIRS

    # Patch cell must be run from the top: `_metadata_similarity` is defined above in this cell.
    _msim = globals().get("_metadata_similarity")
    if _msim is None:
        raise RuntimeError(
            "Missing `_metadata_similarity`. Run the **entire** patch cell "
            "'# === Reliability + Discrimination Patch Overrides' (id `893d6fab`) "
            "from the **first line** so `def _metadata_similarity` executes before "
            "`run_known_pair_benchmark`. Partial selections mid-cell skip that definition."
        )

    cov = float(coverage_penalty_lambda) if coverage_penalty_lambda is not None else float(REDUX3_COVERAGE_PENALTY_LAMBDA)

    def _meta_scorer(q: str, cands: List[str], tm: str):
        mode = str(metadata_reporting_mode or REDUX3_DEFAULT_REPORTING_BENCHMARK).lower()
        if mode == "raw":
            return _msim(
                q,
                cands,
                token=token,
                max_commits=max_commits,
                scoring_mode="family_cosine",
                family_score_norm="raw_cosine",
                coverage_penalty_lambda=cov,
                apply_post_pool_minmax=True,
            )
        if mode in ("contrastive", str(REDUX3_DEFAULT_REPORTING_BENCHMARK).lower()):
            return _metadata_similarity_contrastive_table_aligned(
                q,
                cands,
                token=token,
                max_commits=max_commits,
                windows=REDUX3_METADATA_WINDOWS,
                window_weights=REDUX3_WINDOW_WEIGHTS,
                weights=CAIS_WEIGHTS_STRICT,
                normalization_mode="global_minmax",
                pairwise_scoring=True,
                family_score_norm="raw_cosine",
                coverage_penalty_lambda=cov,
            )
        if mode == "rank_pct":
            return _metadata_similarity_rankpct_pool(
                q,
                cands,
                token=token,
                max_commits=max_commits,
                windows=REDUX3_METADATA_WINDOWS,
                window_weights=REDUX3_WINDOW_WEIGHTS,
                weights=CAIS_WEIGHTS_STRICT,
                normalization_mode="global_minmax",
                pairwise_scoring=True,
                family_score_norm="raw_cosine",
                coverage_penalty_lambda=cov,
            )
        raise ValueError(f"Unknown metadata_reporting_mode: {metadata_reporting_mode!r}")

    methods = {
        "metadata": lambda q, c, tm=None: _meta_scorer(q, c, str(tm or "")),
        "code_centric": lambda q, c, tm=None: code_clone_similarity(q, c, token=token),
        "dynamic": lambda q, c, tm=None: dynamic_behavior_similarity(q, c, token=token),
        "cross_language": lambda q, c, tm=None: deep_code_similarity(q, c, token=token),
    }

    rows: List[Dict[str, object]] = []
    pair_top1_rows: List[Dict[str, object]] = []
    exclusions: List[Dict[str, object]] = []

    print("=" * 88)
    print("KNOWN MIRROR BENCHMARK - Alignment Phase")
    print("=" * 88)

    for pair in pairs:
        name = str(pair.get("name", "unknown"))
        upstream = str(pair.get("upstream_url", ""))
        mirror = str(pair.get("mirror_url", ""))
        negatives = [str(x) for x in list(pair.get("negatives", [])) if str(x).strip()]

        alignment = validate_pair_alignment(pair, token=token)
        if strict_only and alignment.get("status") != "aligned_strict_sha_match":
            exclusions.append({"pair": name, "reason": "strict_only_excluded", **alignment})
            continue
        if not alignment.get("include", False):
            exclusions.append({"pair": name, **alignment})
            continue

        true_match = mirror
        if not _github_slug_from_url(upstream) and _github_slug_from_url(mirror):
            query = mirror
        else:
            query = upstream
        candidates = sorted(list(dict.fromkeys([true_match] + negatives)))

        for method_name, scorer in methods.items():
            ranked = scorer(query, candidates, true_match) or []
            rank_map = _as_rank_dict(ranked)
            tp_rank, tp_score = rank_map.get(true_match, (None, 0.0))

            for cand in candidates:
                rank, score = rank_map.get(cand, (None, 0.0))
                row = {
                    "pair": name,
                    "method": method_name,
                    "query": query,
                    "candidate": cand,
                    "is_true_match": cand == true_match,
                    "label": int(cand == true_match),
                    "rank": rank,
                    "score": float(score),
                    "score_pct": float(score) * 100.0,
                    "true_match_rank": tp_rank,
                    "true_match_score": float(tp_score),
                    "alignment_status": alignment.get("status"),
                    "cc_coverage": BASELINE_COVERAGE.get(cand, {}).get("cc_coverage", np.nan),
                    "dyn_coverage": BASELINE_COVERAGE.get(cand, {}).get("dyn_coverage", np.nan),
                }
                rows.append(row)

            pair_top1_rows.append(
                {
                    "pair": name,
                    "method": method_name,
                    "top1_hit": bool(tp_rank == 1),
                    "top1_repo": ranked[0][0] if ranked else None,
                    "top1_score": float(ranked[0][1]) if ranked else None,
                    "true_match": true_match,
                    "true_match_rank": tp_rank,
                    "alignment_status": alignment.get("status"),
                }
            )

    cand_df = pd.DataFrame(rows)
    top1_df = pd.DataFrame(pair_top1_rows)
    excl_df = pd.DataFrame(exclusions)

    summary = summarize_known_pair_results(cand_df, top1_df)

    if len(cand_df):
        results_dir = Path("results_benchmark")
        results_dir.mkdir(exist_ok=True)
        cand_path = results_dir / f"{save_prefix}_candidate_rows.csv"
        top1_path = results_dir / f"{save_prefix}_top1.csv"
        sum_path = results_dir / f"{save_prefix}_summary.csv"
        exc_path = results_dir / f"{save_prefix}_exclusions.csv"

        cand_df.to_csv(cand_path, index=False)
        top1_df.to_csv(top1_path, index=False)
        summary.to_csv(sum_path, index=False)
        excl_df.to_csv(exc_path, index=False)

        print(f"Saved: {cand_path}")
        print(f"Saved: {top1_path}")
        print(f"Saved: {sum_path}")
        print(f"Saved: {exc_path}")

    return {
        "candidate_rows": cand_df,
        "top1_rows": top1_df,
        "summary": summary,
        "exclusions": excl_df,
    }


def _method_score_percent_for_target(
    query_url: str,
    target_url: str,
    token: Optional[str] = None,
    max_commits: int = 150,
    metadata_windows: Optional[List[int]] = None,
    metadata_window_weights: Optional[Dict[int, float]] = None,
    metadata_weights: Optional[str] = None,
    metadata_extra_candidates: Optional[List[str]] = None,
    include_alt_metadata: bool = False,
    normalization_mode: str = "global_minmax",
    pairwise_scoring: bool = True,
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    reporting_mode: str = REDUX3_DEFAULT_REPORTING_BENCHMARK,
    coverage_penalty_lambda: float = REDUX3_COVERAGE_PENALTY_LAMBDA,
    use_domain_hard_negatives: bool = True,
) -> Dict[str, float]:
    """Return method similarity percentages for one query->target pair.

    ``reporting_mode``:
    - ``rank_pct`` (default): one metadata call on ``{target} + extras + hard negatives`` (filtered),
      then display **rank percentile** among that pool (reduces permissive absolute cosines).
    - ``contrastive``: raw target score vs ``[target]+extras``, then `_contrastive_adjust` vs hard negatives.
    - ``raw``: single-candidate metadata score for target only.
    """
    token = token or github_token
    active_weights = metadata_weights or CAIS_WEIGHTS_STRICT

    hard_negatives_default = (
            _get_domain_hard_negatives(query_url, target_url, token=token)
            if use_domain_hard_negatives
            else list(DEFAULT_METADATA_HARD_NEGATIVES)
        )

    if reporting_mode == "rank_pct":
        extras = list(metadata_extra_candidates or [])
        extras = _filter_metadata_pool_urls(query_url, target_url, extras)
        negs = _filter_metadata_pool_urls(query_url, target_url, list(hard_negatives_default))
        pool = sorted(dict.fromkeys([target_url] + extras + negs))
        meta_ranked = _metadata_similarity(
            query_url,
            pool,
            token=token,
            max_commits=max_commits,
            windows=metadata_windows or REDUX3_METADATA_WINDOWS,
            window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
            weights=active_weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
        )
        meta_pct = _metadata_rank_pct_display(meta_ranked or [], target_url)
    else:
        meta_candidates = [target_url]
        if metadata_extra_candidates:
            for u in metadata_extra_candidates:
                u = str(u).strip()
                if u and u not in meta_candidates:
                    meta_candidates.append(u)
        meta_candidates = sorted(dict.fromkeys(meta_candidates))
        meta_candidates = _filter_metadata_pool_urls(query_url, target_url, meta_candidates)
        if not meta_candidates:
            meta_candidates = [target_url]

        meta_ranked = _metadata_similarity(
            query_url,
            meta_candidates,
            token=token,
            max_commits=max_commits,
            windows=metadata_windows or REDUX3_METADATA_WINDOWS,
            window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
            weights=active_weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
        )
        score_map = {u: float(s) for u, s in (meta_ranked or [])}
        meta_score = float(score_map.get(target_url, 0.0))

        if reporting_mode == "contrastive":
            hn = _filter_metadata_pool_urls(query_url, target_url, list(hard_negatives_default))
            neg_ranked = _metadata_similarity(
                query_url,
                hn,
                token=token,
                max_commits=max_commits,
                windows=metadata_windows or REDUX3_METADATA_WINDOWS,
                window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
                weights=active_weights,
                normalization_mode=normalization_mode,
                pairwise_scoring=pairwise_scoring,
                scoring_mode=metadata_scoring_mode,
                family_score_norm=family_score_norm,
                coverage_penalty_lambda=coverage_penalty_lambda,
            )
            neg_scores = [float(s) for _, s in (neg_ranked or [])]
            meta_score = _contrastive_adjust(meta_score, neg_scores)
        meta_pct = round(float(meta_score) * 100.0, 2)

    result = {"Metadata": float(meta_pct)}

    if include_alt_metadata:
        meta_mimic_ranked = _metadata_similarity(
            query_url,
            [target_url],
            token=token,
            max_commits=max_commits,
            windows=metadata_windows or REDUX3_METADATA_WINDOWS,
            window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
            weights=CAIS_WEIGHTS_MIMIC,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
        )
        mimic_map = {u: float(s) for u, s in (meta_mimic_ranked or [])}
        meta_mimic_score = float(mimic_map.get(target_url, 0.0))
        result["Metadata Mimic"] = round(meta_mimic_score * 100.0, 2)

    cc_ranked = code_clone_similarity(query_url, [target_url], token=token)
    cc_score = float(cc_ranked[0][1]) if cc_ranked else 0.0
    result["Code centric"] = round(cc_score * 100.0, 2)

    dyn_ranked = dynamic_behavior_similarity(query_url, [target_url], token=token)
    dyn_score = float(dyn_ranked[0][1]) if dyn_ranked else 0.0
    result["Dynamic"] = round(dyn_score * 100.0, 2)

    xl_ranked = deep_code_similarity(query_url, [target_url], token=token)
    xl_score = float(xl_ranked[0][1]) if xl_ranked else 0.0
    result["Cross language"] = round(xl_score * 100.0, 2)

    fam_raw = getattr(_metadata_similarity, "last_family_detail", {})
    result["metadata_family_raw"] = fam_raw.get(target_url, {})
    result["api_fail_count"] = API_FAIL_COUNT
    result["cc_coverage"] = BASELINE_COVERAGE.get(target_url, {}).get("cc_coverage", np.nan)
    result["dyn_coverage"] = BASELINE_COVERAGE.get(target_url, {}).get("dyn_coverage", np.nan)

    return result

# --- notebook cell 156 (id=710ee7f3) ---
def build_custom_30_table(
    pairs_path: str = "30_Pairs.json",
    metadata_weights: Optional[str] = None,
    metadata_windows: Optional[List[int]] = None,
    metadata_window_weights: Optional[Dict[int, float]] = None,
    max_commits: int = 150,
    clear_cache_first: bool = False,
    label: str = "Custom 30-pair cohort",
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    reporting_mode: str = REDUX3_DEFAULT_REPORTING_RETRIEVAL,
    coverage_penalty_lambda: float = REDUX3_COVERAGE_PENALTY_LAMBDA,
    use_domain_hard_negatives: bool = True,
) -> pd.DataFrame:
    """Custom 30-pair table; REDUX_3 defaults prioritize calibrated retrieval stability."""
    if clear_cache_first and "CACHE_DIR" in globals():
        shutil.rmtree(CACHE_DIR, ignore_errors=True)
        CACHE_DIR.mkdir(exist_ok=True)
        print(f"Cleared cache: {CACHE_DIR}")

    pairs = _load_custom_pairs(pairs_path)
    repo_urls = _collect_pair_repo_urls(pairs)
    if not repo_urls:
        raise ValueError("Global min-max requires non-empty RepoA/RepoB entries in pairs file.")

    if GLOBAL_NORMALIZER is None:
        fit_global_normalizer(
            repo_urls,
            metrics=CAIS_METRICS,
            token=github_token,
            max_commits=max_commits,
            strategy="minmax",
        )

    rows = []
    for p in pairs:
        ra = str(p.get("RepoA", "")).strip()
        rb = str(p.get("RepoB", "")).strip()
        if not ra or not rb:
            raise ValueError(f"pair ID {p.get('ID')!r}: RepoA and RepoB must be non-empty")

        qurl = _canonical_github_repo_url(ra)
        turl = _canonical_github_repo_url(rb)

        scores = _method_score_percent_for_target(
            qurl,
            turl,
            token=github_token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or REDUX3_METADATA_WINDOWS,
            metadata_window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
            metadata_weights=metadata_weights or CAIS_WEIGHTS_REDUX3_BLEND,
            normalization_mode="global_minmax",
            pairwise_scoring=True,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
            coverage_penalty_lambda=coverage_penalty_lambda,
            use_domain_hard_negatives=use_domain_hard_negatives,
        )

        rows.append({
            "ID": p["ID"],
            "Domain": p.get("Domain", ""),
            "Test": f"{p['ID']}: {ra} vs {rb}",
            "Metadata": scores["Metadata"],
            "Code centric": scores["Code centric"],
            "Dynamic": scores["Dynamic"],
            "Cross language": scores["Cross language"],
            "Query": qurl,
            "Target": turl,
            "TestGroup": label,
        })

    table = pd.DataFrame(rows)
    avg = {
        "ID": "",
        "Domain": "",
        "Test": "Average",
        "Metadata": round(table["Metadata"].mean(), 1),
        "Code centric": round(table["Code centric"].mean(), 1),
        "Dynamic": round(table["Dynamic"].mean(), 1),
        "Cross language": round(table["Cross language"].mean(), 1),
        "Query": "",
        "Target": "",
        "TestGroup": label,
    }
    return pd.concat([table, pd.DataFrame([avg])], ignore_index=True)

# --- notebook cell 163 (id=24fffe55) ---
# === Hard-negative diagnostics + stricter table builder helper ===

def metadata_discrimination_diagnostics(similar_df: pd.DataFrame, dissimilar_df: pd.DataFrame, col: str = "Metadata", threshold: float = 50.0) -> pd.DataFrame:
    """Compute separation, tail, and threshold-oriented discrimination diagnostics."""
    s = similar_df[col].astype(float)
    d = dissimilar_df[col].astype(float)

    gap = float(s.mean() - d.mean()) if len(s) and len(d) else float("nan")
    sim_med = float(s.median()) if len(s) else float("nan")
    overlap = float((d >= sim_med).mean()) if len(d) and not math.isnan(sim_med) else float("nan")

    pooled = np.concatenate([s.values, d.values]) if len(s) and len(d) else np.array([])
    auc_like = float((s.values.reshape(-1, 1) > d.values.reshape(1, -1)).mean()) if len(s) and len(d) else float("nan")
    fpr_like = float((d >= threshold).mean()) if len(d) else float("nan")
    tpr_like = float((s >= threshold).mean()) if len(s) else float("nan")

    out = pd.DataFrame([
        {
            "similar_mean": round(float(s.mean()), 3) if len(s) else np.nan,
            "dissimilar_mean": round(float(d.mean()), 3) if len(d) else np.nan,
            "gap_sim_minus_dissim": round(gap, 3) if not math.isnan(gap) else np.nan,
            "dissim_above_sim_median_rate": round(overlap, 3) if not math.isnan(overlap) else np.nan,
            "dissim_p90": round(float(d.quantile(0.90)), 3) if len(d) else np.nan,
            "dissim_p95": round(float(d.quantile(0.95)), 3) if len(d) else np.nan,
            "threshold": float(threshold),
            "fpr_like": round(fpr_like, 3) if not math.isnan(fpr_like) else np.nan,
            "tpr_like": round(tpr_like, 3) if not math.isnan(tpr_like) else np.nan,
            "auc_like_pairwise": round(auc_like, 3) if not math.isnan(auc_like) else np.nan,
            "metadata_global_std": round(float(np.std(pooled)), 3) if pooled.size else np.nan,
        }
    ])
    return out


def summarize_family_drift(table_df: pd.DataFrame, family_col: str = "metadata_family_raw") -> pd.DataFrame:
    """Summarize mean family contributions across rows with dict payloads."""
    family_vals: Dict[str, List[float]] = {}
    for x in table_df.get(family_col, []):
        if isinstance(x, dict):
            for k, v in x.items():
                try:
                    family_vals.setdefault(k, []).append(float(v))
                except Exception:
                    continue
    rows = [{"family": k, "mean_raw": float(np.mean(v)), "p95_raw": float(np.quantile(v, 0.95)), "n": len(v)} for k, v in family_vals.items() if len(v)]
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("mean_raw", ascending=False).reset_index(drop=True)
    return out


def run_redux3_experiment_matrix(
    pair_defs: List[Tuple[str, str, str]],
    token: Optional[str] = None,
    max_commits: int = 150,
) -> pd.DataFrame:
    """Compact 6-run matrix to evaluate high-leverage REDUX_3 knobs."""
    runs = [
        {"name": "baseline_contrastive", "use_domain_hard_negatives": True, "coverage_penalty_lambda": 0.20, "metadata_window_weights": {50: 0.65, 150: 0.35}, "metadata_weights": CAIS_WEIGHTS_REDUX3_BLEND},
        {"name": "no_domain_negatives", "use_domain_hard_negatives": False, "coverage_penalty_lambda": 0.20, "metadata_window_weights": {50: 0.65, 150: 0.35}, "metadata_weights": CAIS_WEIGHTS_REDUX3_BLEND},
        {"name": "lambda_0_10", "use_domain_hard_negatives": True, "coverage_penalty_lambda": 0.10, "metadata_window_weights": {50: 0.65, 150: 0.35}, "metadata_weights": CAIS_WEIGHTS_REDUX3_BLEND},
        {"name": "lambda_0_30", "use_domain_hard_negatives": True, "coverage_penalty_lambda": 0.30, "metadata_window_weights": {50: 0.65, 150: 0.35}, "metadata_weights": CAIS_WEIGHTS_REDUX3_BLEND},
        {"name": "equal_windows", "use_domain_hard_negatives": True, "coverage_penalty_lambda": 0.20, "metadata_window_weights": {50: 0.50, 150: 0.50}, "metadata_weights": CAIS_WEIGHTS_REDUX3_BLEND},
        {"name": "strict_profile", "use_domain_hard_negatives": True, "coverage_penalty_lambda": 0.20, "metadata_window_weights": {50: 0.65, 150: 0.35}, "metadata_weights": CAIS_WEIGHTS_STRICT},
    ]

    rows = []
    for r in runs:
        tbl = build_argument_table(
            pair_defs,
            known_similarity_pct=0.0,
            token=token,
            max_commits=max_commits,
            metadata_windows=REDUX3_METADATA_WINDOWS,
            metadata_window_weights=r["metadata_window_weights"],
            metadata_weights=r["metadata_weights"],
            reporting_mode="contrastive",
            coverage_penalty_lambda=r["coverage_penalty_lambda"],
            use_domain_hard_negatives=r["use_domain_hard_negatives"],
        )
        m = float(tbl["Metadata"].mean()) if len(tbl) else np.nan
        p95 = float(tbl["Metadata"].quantile(0.95)) if len(tbl) else np.nan
        rows.append({
            "run": r["name"],
            "metadata_mean": round(m, 3),
            "metadata_p95": round(p95, 3),
            "coverage_penalty_lambda": r["coverage_penalty_lambda"],
            "use_domain_hard_negatives": r["use_domain_hard_negatives"],
            "window_weights": str(r["metadata_window_weights"]),
        })
    return pd.DataFrame(rows)


def build_custom_30_table_strict(
    pairs_path: str = "30_Pairs.json",
    metadata_weights: Optional[str] = None,
    metadata_windows: Optional[List[int]] = None,
    metadata_window_weights: Optional[Dict[int, float]] = None,
    max_commits: int = 150,
    clear_cache_first: bool = False,
    label: str = "Custom 30-pair cohort (strict)",
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    reporting_mode: str = REDUX3_DEFAULT_REPORTING_BENCHMARK,
    coverage_penalty_lambda: float = REDUX3_COVERAGE_PENALTY_LAMBDA,
    use_domain_hard_negatives: bool = True,
) -> pd.DataFrame:
    """Strict wrapper around existing table builder path with calibrated metadata reporting."""
    if clear_cache_first and "CACHE_DIR" in globals():
        shutil.rmtree(CACHE_DIR, ignore_errors=True)
        CACHE_DIR.mkdir(exist_ok=True)

    pairs = _load_custom_pairs(pairs_path)
    rows = []
    for p in pairs:
        ra = str(p.get("RepoA", "")).strip()
        rb = str(p.get("RepoB", "")).strip()
        if not ra or not rb:
            continue
        qurl = _canonical_github_repo_url(ra)
        turl = _canonical_github_repo_url(rb)

        scores = _method_score_percent_for_target(
            qurl,
            turl,
            token=github_token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or REDUX3_METADATA_WINDOWS,
            metadata_window_weights=metadata_window_weights or REDUX3_WINDOW_WEIGHTS,
            metadata_weights=metadata_weights or CAIS_WEIGHTS_REDUX3_BLEND,
            normalization_mode="global_minmax",
            pairwise_scoring=True,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
            coverage_penalty_lambda=coverage_penalty_lambda,
            use_domain_hard_negatives=use_domain_hard_negatives,
        )

        rows.append(
            {
                "ID": p.get("ID", ""),
                "Domain": p.get("Domain", ""),
                "Test": f"{p.get('ID', '')}: {ra} vs {rb}",
                "Metadata": scores.get("Metadata", np.nan),
                "Code centric": scores.get("Code centric", np.nan),
                "Dynamic": scores.get("Dynamic", np.nan),
                "Cross language": scores.get("Cross language", np.nan),
                "cc_coverage": scores.get("cc_coverage", np.nan),
                "dyn_coverage": scores.get("dyn_coverage", np.nan),
                "api_fail_count": scores.get("api_fail_count", np.nan),
                "metadata_family_raw": scores.get("metadata_family_raw", {}),
                "Query": qurl,
                "Target": turl,
                "TestGroup": label,
            }
        )

    table = pd.DataFrame(rows)
    if len(table):
        avg = {
            "ID": "",
            "Domain": "",
            "Test": "Average",
            "Metadata": round(float(table["Metadata"].mean()), 2),
            "Code centric": round(float(table["Code centric"].mean()), 2),
            "Dynamic": round(float(table["Dynamic"].mean()), 2),
            "Cross language": round(float(table["Cross language"].mean()), 2),
            "cc_coverage": round(float(table["cc_coverage"].mean()), 3),
            "dyn_coverage": round(float(table["dyn_coverage"].mean()), 3),
            "api_fail_count": int(API_FAIL_COUNT),
            "metadata_family_raw": {},
            "Query": "",
            "Target": "",
            "TestGroup": label,
        }
        table = pd.concat([table, pd.DataFrame([avg])], ignore_index=True)

    return table
