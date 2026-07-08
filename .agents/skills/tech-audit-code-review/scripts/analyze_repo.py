#!/usr/bin/env python3
"""
analyze_repo.py — Static analysis of a code repository to produce five engineering health metrics.

Usage:
    python analyze_repo.py <repo_root> --output metrics.json

All metrics are derived from repository contents (source files, git history, config files)
with zero external service dependencies. Each metric includes a confidence field.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Language detection & file classification
# ---------------------------------------------------------------------------

LANG_EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "javascript",
    ".tsx": "typescript", ".java": "java", ".go": "go", ".rb": "ruby", ".rs": "rust",
    ".c": "c", ".cpp": "cpp", ".h": "cpp", ".cs": "csharp", ".php": "php",
    ".swift": "swift", ".kt": "kotlin", ".scala": "scala", ".sh": "bash",
    ".r": "r", ".R": "r", ".lua": "lua", ".pl": "perl", ".ex": "elixir",
    ".exs": "elixir", ".erl": "erlang", ".hs": "haskell", ".dart": "dart",
    ".vue": "vue", ".svelte": "svelte",
}

TEST_PATTERNS = [
    re.compile(r"test_[^/]+\.py$"),
    re.compile(r"[^/]+_test\.py$"),
    re.compile(r"[^/]+_test\.go$"),
    re.compile(r"[^/]+\.test\.[jt]sx?$"),
    re.compile(r"[^/]+\.spec\.[jt]sx?$"),
    re.compile(r"[^/]+Test\.java$"),
    re.compile(r"[^/]+_spec\.rb$"),
    re.compile(r"[^/]+\.test\.rs$"),
]

TEST_DIRS = {"__tests__", "tests", "test", "spec", "testing", "test_suite"}

VENDORED_DIRS = {
    "node_modules", "vendor", ".venv", "venv", "env", ".env", "__pycache__",
    ".git", ".svn", ".hg", "dist", "build", "out", ".next", ".nuxt",
    "target", "bin", "obj", "coverage", ".tox", "egg-info",
    "site-packages", "bower_components", ".yarn", ".pnp",
}

GENERATED_PATTERNS = [
    re.compile(r"\.min\.[jc]ss?$"),
    re.compile(r"\.bundle\.js$"),
    re.compile(r"package-lock\.json$"),
    re.compile(r"yarn\.lock$"),
    re.compile(r"\.lock$"),
    re.compile(r"\.map$"),
]

# ---------------------------------------------------------------------------
# Vulnerability patterns
# ---------------------------------------------------------------------------

SECRET_PATTERNS = [
    re.compile(r"""(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)\s*[:=]\s*['"][A-Za-z0-9+/=_\-]{16,}['"]""", re.I),
    re.compile(r"""(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]{8,}['"]""", re.I),
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
    re.compile(r"ghp_[A-Za-z0-9]{36}"),  # GitHub PAT
    re.compile(r"sk-[A-Za-z0-9]{32,}"),  # OpenAI / Stripe secret key
    re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----"),
]

DANGEROUS_FUNCTIONS = {
    "python": [
        (re.compile(r"\beval\s*\("), "eval() call"),
        (re.compile(r"\bexec\s*\("), "exec() call"),
        (re.compile(r"subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True"), "subprocess with shell=True"),
        (re.compile(r"os\.system\s*\("), "os.system() call"),
        (re.compile(r"pickle\.loads?\s*\("), "pickle deserialization"),
        (re.compile(r"""cursor\.execute\s*\(\s*(?:f['"]|['"].*%s|['"].*\+)"""), "SQL injection risk"),
        (re.compile(r"verify\s*=\s*False"), "TLS verification disabled"),
    ],
    "javascript": [
        (re.compile(r"\beval\s*\("), "eval() call"),
        (re.compile(r"innerHTML\s*="), "innerHTML assignment"),
        (re.compile(r"dangerouslySetInnerHTML"), "dangerouslySetInnerHTML"),
        (re.compile(r"document\.write\s*\("), "document.write()"),
        (re.compile(r"new\s+Function\s*\("), "Function constructor"),
    ],
    "typescript": [],  # inherits javascript
    "go": [
        (re.compile(r"fmt\.Sprintf\s*\(.*\+"), "potential format string injection"),
        (re.compile(r"InsecureSkipVerify:\s*true"), "TLS verification disabled"),
    ],
    "java": [
        (re.compile(r"Runtime\.getRuntime\(\)\.exec"), "Runtime.exec()"),
        (re.compile(r"ObjectInputStream"), "Java deserialization"),
        (re.compile(r"Statement.*execute(?:Query|Update)?\s*\(.*\+"), "SQL injection risk"),
    ],
    "ruby": [
        (re.compile(r"\beval\s*\("), "eval() call"),
        (re.compile(r"system\s*\("), "system() call"),
        (re.compile(r"`[^`]*\#\{"), "command injection via backticks"),
    ],
    "c": [
        (re.compile(r"\bgets\s*\("), "gets() — buffer overflow"),
        (re.compile(r"\bstrcpy\s*\("), "strcpy() — no bounds checking"),
        (re.compile(r"\bsprintf\s*\("), "sprintf() — no bounds checking"),
    ],
    "cpp": [],  # inherits c
}

# Copy parent patterns to child languages
DANGEROUS_FUNCTIONS["typescript"] += DANGEROUS_FUNCTIONS["javascript"]
DANGEROUS_FUNCTIONS["cpp"] += DANGEROUS_FUNCTIONS["c"]
DANGEROUS_FUNCTIONS.setdefault("jsx", DANGEROUS_FUNCTIONS["javascript"])
DANGEROUS_FUNCTIONS.setdefault("tsx", DANGEROUS_FUNCTIONS["typescript"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_vendored(path_parts):
    return any(part in VENDORED_DIRS for part in path_parts)

def is_generated(filename):
    return any(p.search(filename) for p in GENERATED_PATTERNS)

def is_test_file(rel_path):
    parts = Path(rel_path).parts
    if any(p.lower() in TEST_DIRS for p in parts):
        return True
    fname = os.path.basename(rel_path)
    return any(p.search(fname) for p in TEST_PATTERNS)

def count_lines(filepath):
    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*", "*", "<!--"))]
        return len(lines), len(code_lines), lines
    except Exception:
        return 0, 0, []

def git_available(repo_root):
    try:
        subprocess.run(["git", "-C", repo_root, "rev-parse", "--git-dir"],
                       capture_output=True, check=True, timeout=5)
        return True
    except Exception:
        return False

def git_log(repo_root, args, max_count=500):
    try:
        cmd = ["git", "-C", repo_root, "log"] + args + [f"--max-count={max_count}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception:
        return ""

# ---------------------------------------------------------------------------
# File inventory
# ---------------------------------------------------------------------------

def scan_files(repo_root):
    """Walk the repo and classify every source file."""
    source_files = []  # (rel_path, language, is_test)
    for root, dirs, files in os.walk(repo_root):
        # prune vendored dirs in place
        dirs[:] = [d for d in dirs if d not in VENDORED_DIRS and not d.startswith(".")]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, repo_root)
            parts = Path(rel).parts
            if is_vendored(parts) or is_generated(fname):
                continue
            ext = os.path.splitext(fname)[1].lower()
            lang = LANG_EXTENSIONS.get(ext)
            if lang:
                source_files.append((rel, lang, is_test_file(rel)))
    return source_files

# ---------------------------------------------------------------------------
# Metric 1 — Vulnerability Density
# ---------------------------------------------------------------------------

def analyze_vulnerabilities(repo_root, source_files):
    total_loc = 0
    findings = []

    for rel, lang, is_test in source_files:
        if is_test:
            continue
        full = os.path.join(repo_root, rel)
        _, cloc, lines = count_lines(full)
        total_loc += cloc
        content = "".join(lines)

        # Secrets
        for pat in SECRET_PATTERNS:
            for m in pat.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no, "type": "hardcoded_secret",
                    "detail": "Potential hardcoded secret/credential", "weight": 3,
                })

        # Dangerous functions
        patterns = DANGEROUS_FUNCTIONS.get(lang, [])
        for pat, desc in patterns:
            for m in pat.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no, "type": "dangerous_function",
                    "detail": desc, "weight": 2,
                })

    # Check for lockfiles (dependency hygiene)
    lockfiles = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                 "Pipfile.lock", "poetry.lock", "Gemfile.lock",
                 "go.sum", "Cargo.lock", "composer.lock"]
    has_lockfile = any(os.path.isfile(os.path.join(repo_root, lf)) for lf in lockfiles)

    kloc = max(total_loc / 1000, 0.001)
    weighted = sum(f["weight"] for f in findings)
    value = round(weighted / kloc, 3)

    categories = Counter(f["type"] for f in findings)

    if total_loc > 1000 and has_lockfile:
        confidence = "high"
    elif total_loc > 500:
        confidence = "medium"
    else:
        confidence = "low"

    rating = "elite" if value == 0 else "good" if value < 0.5 else "fair" if value < 2 else "poor"

    return {
        "value": value,
        "unit": "per_kloc",
        "rating": rating,
        "confidence": confidence,
        "details": {
            "loc": total_loc,
            "kloc": round(kloc, 3),
            "findings_count": len(findings),
            "weighted_score": weighted,
            "categories": dict(categories),
            "top_findings": sorted(findings, key=lambda f: -f["weight"])[:10],
        },
    }

# ---------------------------------------------------------------------------
# Metric 2 — Change Failure Rate
# ---------------------------------------------------------------------------

def analyze_cfr(repo_root):
    if not git_available(repo_root):
        return _no_git_metric("change_failure_rate", "percent")

    # Get merge commits (last 6 months)
    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
    merge_log = git_log(repo_root, [
        "--merges", "--format=%H|%aI|%s", f"--since={six_months_ago}",
    ])
    merges = []
    for line in merge_log.splitlines():
        if "|" in line:
            parts = line.split("|", 2)
            if len(parts) == 3:
                merges.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})

    # Get all commits for revert/hotfix detection
    all_log = git_log(repo_root, [
        "--format=%H|%aI|%s", f"--since={six_months_ago}",
    ])
    all_commits = []
    for line in all_log.splitlines():
        if "|" in line:
            parts = line.split("|", 2)
            if len(parts) == 3:
                all_commits.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})

    revert_pattern = re.compile(r"(?:revert|reverts?)\b", re.I)
    hotfix_pattern = re.compile(r"\b(?:fix|hotfix|patch|urgent|bug)\b", re.I)

    if len(merges) >= 10:
        reverts = [c for c in all_commits if revert_pattern.search(c["subject"])]
        # Hotfixes: non-merge commits with fix-like language
        hotfixes = [c for c in all_commits
                    if hotfix_pattern.search(c["subject"])
                    and c["hash"] not in {m["hash"] for m in merges}
                    and not revert_pattern.search(c["subject"])]
        # Rough heuristic: count unique hotfix events (dedupe by day)
        hotfix_days = set()
        unique_hotfixes = []
        for h in hotfixes:
            day = h["date"][:10]
            if day not in hotfix_days:
                hotfix_days.add(day)
                unique_hotfixes.append(h)

        total_failures = len(reverts) + len(unique_hotfixes)
        commit_count = len(merges) if len(merges) + total_failures == len(all_commits) else len(all_commits)
        value = round((total_failures / commit_count) * 100, 1)
        confidence = "high" if len(merges) >= 50 else "medium"
        failure_hashes = [c["hash"][:7] for c in reverts + unique_hotfixes][:20]
    else:
        # Fallback: ratio of fix-like commits
        fixes = [c for c in all_commits if hotfix_pattern.search(c["subject"]) or revert_pattern.search(c["subject"])]
        value = round((len(fixes) / max(len(all_commits), 1)) * 100, 1)
        confidence = "low"
        failure_hashes = [c["hash"][:7] for c in fixes][:20]
        merges = all_commits  # for counting purposes
        reverts = [c for c in all_commits if revert_pattern.search(c["subject"])]
        unique_hotfixes = fixes

    rating = "elite" if value < 5 else "good" if value < 10 else "fair" if value < 20 else "poor"

    return {
        "value": value,
        "unit": "percent",
        "rating": rating,
        "confidence": confidence,
        "details": {
            "total_merges": len(merges),
            "reverts": len(reverts) if 'reverts' in dir() else 0,
            "hotfixes": len(unique_hotfixes) if 'unique_hotfixes' in dir() else 0,
            "failure_commits": failure_hashes,
            "analysis_window": "last 6 months",
        },
    }

# ---------------------------------------------------------------------------
# Metric 3 — Lead Time for Changes (DORA)
# ---------------------------------------------------------------------------

def analyze_lead_time(repo_root):
    if not git_available(repo_root):
        return _no_git_metric("lead_time_for_changes", "hours")

    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")

    # Attempt 1: merge-based lead time
    merge_log = git_log(repo_root, [
        "--merges", "--format=%H|%aI", f"--since={six_months_ago}",
    ])
    merge_hashes = []
    merge_dates = []
    for line in merge_log.splitlines():
        if "|" in line:
            h, d = line.split("|", 1)
            merge_hashes.append(h.strip())
            merge_dates.append(d.strip())

    lead_times = []
    for mh, md in zip(merge_hashes, merge_dates):
        try:
            # Find the first parent commit timestamp (branch point approximation)
            parents = subprocess.run(
                ["git", "-C", repo_root, "log", "--format=%aI", f"{mh}..{mh}~1", "--reverse", "--max-count=1"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if not parents:
                # Try alternative: second parent's oldest commit
                result = subprocess.run(
                    ["git", "-C", repo_root, "rev-list", "--reverse", f"{mh}^2", "--not", f"{mh}^1", "--max-count=1"],
                    capture_output=True, text=True, timeout=10,
                )
                first_commit = result.stdout.strip()
                if first_commit:
                    fc_date = subprocess.run(
                        ["git", "-C", repo_root, "log", "-1", "--format=%aI", first_commit],
                        capture_output=True, text=True, timeout=10,
                    ).stdout.strip()
                    if fc_date:
                        parents = fc_date

            if parents:
                first_line = parents.splitlines()[0]
                t_start = datetime.fromisoformat(first_line)
                t_merge = datetime.fromisoformat(md)
                delta_hours = max((t_merge - t_start).total_seconds() / 3600, 0)
                if delta_hours < 8760:  # ignore > 1 year
                    lead_times.append(delta_hours)
        except Exception:
            continue

    if len(lead_times) >= 10:
        lead_times.sort()
        median = lead_times[len(lead_times) // 2]
        p90 = lead_times[int(len(lead_times) * 0.9)]
        confidence = "high" if len(lead_times) >= 30 else "medium"
    elif len(lead_times) > 0:
        median = lead_times[len(lead_times) // 2]
        p90 = lead_times[-1]
        confidence = "low"
    else:
        # Fallback: inter-commit cadence
        cadence_log = git_log(repo_root, ["--format=%aI", f"--since={six_months_ago}"])
        dates = []
        for line in cadence_log.splitlines():
            line = line.strip()
            if line:
                try:
                    dates.append(datetime.fromisoformat(line))
                except Exception:
                    pass
        if len(dates) >= 2:
            dates.sort()
            deltas = [(dates[i] - dates[i - 1]).total_seconds() / 3600 for i in range(1, len(dates))]
            median = sorted(deltas)[len(deltas) // 2]
            p90 = sorted(deltas)[int(len(deltas) * 0.9)]
        else:
            median = 0
            p90 = 0
        lead_times = []
        confidence = "low"

    value = round(median, 1)
    rating = "elite" if value < 24 else "good" if value < 72 else "fair" if value < 168 else "poor"

    return {
        "value": value,
        "unit": "hours",
        "rating": rating,
        "confidence": confidence,
        "details": {
            "merge_count": len(lead_times),
            "median_hours": round(median, 1),
            "p90_hours": round(p90, 1) if lead_times else None,
            "shortest_hours": round(min(lead_times), 1) if lead_times else None,
            "longest_hours": round(max(lead_times), 1) if lead_times else None,
            "analysis_window": "last 6 months",
        },
    }

# ---------------------------------------------------------------------------
# Metric 4 — Technical Debt Ratio
# ---------------------------------------------------------------------------

def analyze_tdr(repo_root, source_files):
    total_loc = 0
    issues = defaultdict(int)
    remediation_minutes = 0

    for rel, lang, is_test in source_files:
        if is_test:
            continue
        full = os.path.join(repo_root, rel)
        total_lines, cloc, lines = count_lines(full)
        total_loc += cloc

        # Long files (> 500 lines)
        if cloc > 500:
            issues["long_files"] += 1
            remediation_minutes += 60

        # Long functions (simplified: count indented blocks > 50 lines)
        func_len = 0
        in_func = False
        for line in lines:
            stripped = line.rstrip()
            if not stripped:
                continue
            indent = len(line) - len(line.lstrip())
            # Heuristic: function-like start
            if re.match(r"\s*(def |function |func |fn |public |private |protected |static |\w+\s*\()", stripped):
                if in_func and func_len > 50:
                    issues["long_functions"] += 1
                    remediation_minutes += 30
                func_len = 0
                in_func = True
            elif in_func:
                func_len += 1
        if in_func and func_len > 50:
            issues["long_functions"] += 1
            remediation_minutes += 30

        # Deep nesting
        for line in lines:
            indent = len(line) - len(line.lstrip())
            spaces_per_level = 4  # assume 4-space indent
            depth = indent // spaces_per_level if spaces_per_level > 0 else 0
            if depth > 4 and any(kw in line for kw in ("if ", "for ", "while ", "switch ", "match ")):
                issues["deep_nesting"] += 1
                remediation_minutes += 20

        # TODO/FIXME/HACK comments
        for line in lines:
            if re.search(r"\b(TODO|FIXME|HACK|XXX|KLUDGE)\b", line):
                issues["todo_comments"] += 1
                remediation_minutes += 10

    # Duplicated blocks (hash 6-line windows)
    block_hashes = defaultdict(list)
    for rel, lang, is_test in source_files:
        if is_test:
            continue
        full = os.path.join(repo_root, rel)
        _, _, lines = count_lines(full)
        code_lines = [l.strip() for l in lines if l.strip()]
        for i in range(len(code_lines) - 5):
            block = "\n".join(code_lines[i:i + 6])
            h = hashlib.md5(block.encode()).hexdigest()
            block_hashes[h].append((rel, i + 1))

    dup_count = sum(1 for h, locs in block_hashes.items() if len(locs) > 1)
    issues["duplicated_blocks"] = dup_count
    remediation_minutes += dup_count * 15

    dev_minutes = max(total_loc * 0.5, 1)
    value = round((remediation_minutes / dev_minutes) * 100, 1)
    total_issues = sum(issues.values())

    if total_loc > 5000:
        confidence = "high"
    elif total_loc > 1000:
        confidence = "medium"
    else:
        confidence = "low"

    rating = "elite" if value < 5 else "good" if value < 10 else "fair" if value < 20 else "poor"

    return {
        "value": value,
        "unit": "percent",
        "rating": rating,
        "confidence": confidence,
        "details": {
            "total_issues": total_issues,
            "remediation_minutes": remediation_minutes,
            "development_minutes": round(dev_minutes),
            "breakdown": dict(issues),
        },
    }

# ---------------------------------------------------------------------------
# Metric 5 — Automated Test Coverage
# ---------------------------------------------------------------------------

def analyze_test_coverage(repo_root, source_files):
    test_files = [(r, l) for r, l, t in source_files if t]
    src_files = [(r, l) for r, l, t in source_files if not t]

    test_loc = 0
    for rel, _ in test_files:
        full = os.path.join(repo_root, rel)
        _, cloc, _ = count_lines(full)
        test_loc += cloc

    src_loc = 0
    for rel, _ in src_files:
        full = os.path.join(repo_root, rel)
        _, cloc, _ = count_lines(full)
        src_loc += cloc

    test_ratio = test_loc / max(src_loc, 1)
    structural_score = min(test_ratio / 0.3, 1.0) * 100  # 30%+ test ratio = 100

    # Business-path heuristic
    all_test_content = ""
    for rel, _ in test_files:
        full = os.path.join(repo_root, rel)
        try:
            with open(full, "r", errors="replace") as f:
                all_test_content += f.read().lower() + "\n"
        except Exception:
            pass

    business_paths = {
        "auth": bool(re.search(r"\b(auth|login|logout|session|token|jwt|oauth|signin|signup)\b", all_test_content)),
        "payment": bool(re.search(r"\b(payment|billing|invoice|charge|stripe|paypal|checkout|subscription)\b", all_test_content)),
        "validation": bool(re.search(r"\b(validat|sanitiz|schema|constraint|required|format|assert)\b", all_test_content)),
        "error_handling": bool(re.search(r"\b(error|exception|raise|throw|catch|reject|fail|assert.*error)\b", all_test_content)),
        "api_endpoints": bool(re.search(r"\b(get|post|put|delete|patch|request|response|endpoint|route|api)\b", all_test_content)),
    }

    bp_score = sum(1 for v in business_paths.values() if v) * 20
    composite = round(0.6 * structural_score + 0.4 * bp_score, 1)

    if len(test_files) > 20:
        confidence = "high"
    elif len(test_files) > 5:
        confidence = "medium"
    else:
        confidence = "low"

    rating = "elite" if composite > 80 else "good" if composite > 60 else "fair" if composite > 40 else "poor"

    return {
        "value": composite,
        "unit": "percent",
        "rating": rating,
        "confidence": confidence,
        "details": {
            "test_files": len(test_files),
            "test_loc": test_loc,
            "source_loc": src_loc,
            "test_ratio": round(test_ratio, 3),
            "business_paths": business_paths,
            "business_path_score": bp_score,
            "structural_score": round(structural_score, 1),
            "composite_score": composite,
        },
    }

# ---------------------------------------------------------------------------
# No-git fallback
# ---------------------------------------------------------------------------

def _no_git_metric(name, unit):
    return {
        "value": 0,
        "unit": unit,
        "rating": "fair",
        "confidence": "low",
        "details": {
            "note": "Git history not available — metric could not be computed.",
        },
    }

# ---------------------------------------------------------------------------
# Summary score
# ---------------------------------------------------------------------------

RATING_SCORES = {"elite": 100, "good": 75, "fair": 50, "poor": 25}
WEIGHTS = {
    "vulnerability_density": 0.25,
    "change_failure_rate": 0.20,
    "lead_time_for_changes": 0.15,
    "technical_debt_ratio": 0.20,
    "test_coverage": 0.20,
}

def compute_summary(metrics):
    score = 0
    for key, weight in WEIGHTS.items():
        rating = metrics[key]["rating"]
        score += RATING_SCORES.get(rating, 50) * weight
    return round(score, 1)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Analyze a code repository for engineering health metrics.")
    parser.add_argument("repo_root", help="Path to the repository root")
    parser.add_argument("--output", "-o", default="metrics.json", help="Output JSON file path")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    if not os.path.isdir(repo_root):
        print(f"Error: {repo_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {repo_root} ...", file=sys.stderr)
    source_files = scan_files(repo_root)
    print(f"Found {len(source_files)} source files ({sum(1 for _, _, t in source_files if t)} test files)", file=sys.stderr)

    langs = Counter(lang for _, lang, _ in source_files)
    print(f"Languages: {dict(langs.most_common(5))}", file=sys.stderr)

    print("Analyzing vulnerability density ...", file=sys.stderr)
    vuln = analyze_vulnerabilities(repo_root, source_files)

    print("Analyzing change failure rate ...", file=sys.stderr)
    cfr = analyze_cfr(repo_root)

    print("Analyzing lead time for changes ...", file=sys.stderr)
    lead = analyze_lead_time(repo_root)

    print("Analyzing technical debt ratio ...", file=sys.stderr)
    tdr = analyze_tdr(repo_root, source_files)

    print("Analyzing test coverage ...", file=sys.stderr)
    coverage = analyze_test_coverage(repo_root, source_files)

    metrics = {
        "vulnerability_density": vuln,
        "change_failure_rate": cfr,
        "lead_time_for_changes": lead,
        "technical_debt_ratio": tdr,
        "test_coverage": coverage,
    }

    repo_name = os.path.basename(repo_root)
    result = {
        "repository": repo_name,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "summary_score": compute_summary(metrics),
        "metrics": metrics,
    }

    output_path = os.path.abspath(args.output)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults written to {output_path}", file=sys.stderr)
    print(f"Summary score: {result['summary_score']}/100", file=sys.stderr)
    for key, m in metrics.items():
        print(f"  {key}: {m['value']} {m['unit']} ({m['rating']}, confidence: {m['confidence']})", file=sys.stderr)

if __name__ == "__main__":
    main()
