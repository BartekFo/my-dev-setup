# Metrics Specification

Detailed computation logic for each of the five code-health metrics. The analysis script
(`scripts/analyze_repo.py`) implements these algorithms. Every metric produces a standardized
JSON block with `value`, `unit`, `rating`, `confidence`, and `details`.

---

## 1. Vulnerability Density

**Definition**: Number of critical/high-severity security issues per 1,000 lines of code (KLOC).

### Computation

1. Count total lines of code (LOC) excluding blank lines, comments, and vendored/generated files.
2. Scan for vulnerability indicators:
   - **Hardcoded secrets**: regex patterns for API keys, tokens, passwords in source.
   - **Dangerous functions**: language-specific sinks (`eval`, `exec`, `innerHTML`,
     `dangerouslySetInnerHTML`, `os.system`, `subprocess.call` with `shell=True`,
     SQL string concatenation, `gets()`, `strcpy()`, etc.).
   - **Insecure dependencies**: parse lockfiles (`package-lock.json`, `Pipfile.lock`,
     `Gemfile.lock`, `go.sum`, `Cargo.lock`) and flag packages with known CVEs using a
     bundled list of high-profile vulnerable versions. If no lockfile exists, check
     version-pinning hygiene.
   - **Missing security headers / CSP**: for web projects, check for helmet/CSP config.
   - **Insecure TLS/crypto usage**: deprecated algorithms, `verify=False`, etc.
3. Weight findings: hardcoded secret = 3, dangerous function without sanitization = 2,
   insecure dep = 2, minor hygiene issue = 1.
4. `value = (weighted_count / LOC) * 1000`

### Rating bands

| Rating | Value |
|--------|-------|
| Elite  | 0 |
| Good   | < 0.5 |
| Fair   | < 2.0 |
| Poor   | ≥ 2.0 |

### Confidence

- `high` if LOC > 1000 and at least one lockfile was parsed.
- `medium` if LOC > 500.
- `low` otherwise.

### Details payload

```json
{
  "loc": 12345,
  "kloc": 12.345,
  "findings_count": 7,
  "weighted_score": 14,
  "categories": {
    "hardcoded_secrets": 1,
    "dangerous_functions": 3,
    "insecure_dependencies": 2,
    "other": 1
  },
  "top_findings": [
    {"file": "src/db.py", "line": 42, "type": "dangerous_function", "detail": "SQL string concatenation"},
    ...
  ]
}
```

---

## 2. Change Failure Rate (CFR)

**Definition**: Percentage of changes (merge commits) that were followed by a revert or an
immediate hotfix commit.

### Computation

1. Parse git log for merge commits on the default branch.
2. Identify reverts: commits whose message matches `Revert "..."` or `revert:`.
3. Identify hotfixes: commits within 2 hours of a merge whose message contains `fix`, `hotfix`,
   `patch`, `urgent`, or `bug` (case-insensitive) and that touch the same files.
4. `value = (reverts + hotfixes) / total_merges * 100`

### Fallback (no merge history)

If the repo has < 10 merge commits, fall back to counting the ratio of commits whose message
contains fix/revert language to total commits. Mark confidence as `low`.

### Rating bands

| Rating | Value |
|--------|-------|
| Elite  | < 5% |
| Good   | < 10% |
| Fair   | < 20% |
| Poor   | ≥ 20% |

### Confidence

- `high` if ≥ 50 merge commits.
- `medium` if ≥ 10 merge commits.
- `low` otherwise (using fallback).

### Details payload

```json
{
  "total_merges": 120,
  "reverts": 4,
  "hotfixes": 6,
  "failure_commits": ["abc1234", "def5678", ...],
  "analysis_window": "last 6 months"
}
```

---

## 3. Lead Time for Changes (DORA)

**Definition**: Median elapsed time (in hours) from the first commit on a feature branch to
its merge into the default branch.

### Computation

1. Identify merge commits on the default branch.
2. For each merge, walk back to find the first divergence point from the base branch.
3. Compute `delta = merge_timestamp - first_commit_timestamp` in hours.
4. Report the **median** of all deltas.

### Fallback

If no merge commits exist (e.g., trunk-based development or squash-merge workflow), use the
inter-commit cadence on the default branch as a proxy for deployment frequency.
Mark confidence as `low`.

### Rating bands

| Rating | Value |
|--------|-------|
| Elite  | < 24 hours |
| Good   | < 72 hours |
| Fair   | < 168 hours (1 week) |
| Poor   | ≥ 168 hours |

### Confidence

- `high` if ≥ 30 merges with clear branch history.
- `medium` if ≥ 10 merges.
- `low` if using fallback.

### Details payload

```json
{
  "merge_count": 85,
  "median_hours": 18.4,
  "p90_hours": 52.1,
  "shortest_hours": 0.5,
  "longest_hours": 312.0,
  "analysis_window": "last 6 months"
}
```

---

## 4. Technical Debt Ratio (TDR)

**Definition**: Estimated cost to remediate code-quality issues as a percentage of total
development effort.

### Computation

Uses a simplified SQALE-inspired approach:

1. **Code smells** (each adds estimated remediation minutes):
   - Functions > 50 lines → 30 min each
   - Files > 500 lines → 60 min each
   - Cyclomatic complexity proxy (nested if/for/while depth > 4) → 20 min each
   - Duplicated blocks (detected via simple hash-based comparison of 6+ line blocks) → 15 min each
   - TODO/FIXME/HACK/XXX comments → 10 min each
   - Unused imports (Python/JS) → 5 min each
2. **Total remediation minutes** = sum of all issue costs.
3. **Total development effort** estimated as LOC × 0.5 min/line (industry median).
4. `value = (remediation_minutes / development_minutes) * 100`

### Rating bands

| Rating | Value |
|--------|-------|
| Elite  | < 5% |
| Good   | < 10% |
| Fair   | < 20% |
| Poor   | ≥ 20% |

### Confidence

- `high` if LOC > 5000.
- `medium` if LOC > 1000.
- `low` otherwise.

### Details payload

```json
{
  "total_issues": 142,
  "remediation_minutes": 3400,
  "development_minutes": 45000,
  "breakdown": {
    "long_functions": 12,
    "long_files": 3,
    "deep_nesting": 18,
    "duplicated_blocks": 8,
    "todo_comments": 95,
    "unused_imports": 6
  }
}
```

---

## 5. Automated Test Coverage

**Definition**: Weighted blend of structural test presence and business-path coverage heuristic.

### Computation

Rather than running a coverage tool (which requires project-specific setup), the skill
estimates coverage from repository structure:

1. **Test file ratio**: Identify test files by convention (`test_*.py`, `*_test.go`,
   `*.test.js`, `*.spec.ts`, `*Test.java`, files under `__tests__/`, `tests/`, `test/`,
   `spec/` directories). Compute `test_loc / total_loc`.
2. **Business-path heuristic**: Look for tests that exercise critical paths:
   - Auth/login tests (files/functions mentioning auth, login, session, token)
   - Payment/billing tests
   - Data validation tests
   - Error handling tests (try/catch density in test files, error/exception assertions)
   - API endpoint tests (HTTP method references in test files)
   Score each category present as 20% → sum gives business path score (0-100%).
3. **Final score**: `0.6 × test_file_ratio_normalized + 0.4 × business_path_score`
   where `test_file_ratio_normalized` maps the ratio to 0-100 (ratio of 0.3+ = 100%).

### Rating bands

| Rating | Value |
|--------|-------|
| Elite  | > 80% |
| Good   | > 60% |
| Fair   | > 40% |
| Poor   | ≤ 40% |

### Confidence

- `high` if > 20 test files found.
- `medium` if > 5 test files.
- `low` otherwise.

### Details payload

```json
{
  "test_files": 48,
  "test_loc": 5200,
  "source_loc": 18000,
  "test_ratio": 0.289,
  "business_paths": {
    "auth": true,
    "payment": false,
    "validation": true,
    "error_handling": true,
    "api_endpoints": true
  },
  "business_path_score": 80,
  "structural_score": 96,
  "composite_score": 89.6
}
```

---

## Summary Score

The overall repository health score is a weighted average:

| Metric | Weight |
|--------|--------|
| Vulnerability Density | 25% |
| Change Failure Rate   | 20% |
| Lead Time for Changes | 15% |
| Technical Debt Ratio  | 20% |
| Test Coverage         | 20% |

Each metric's rating maps to a 0-100 sub-score:
- Elite = 100
- Good = 75
- Fair = 50
- Poor = 25

`summary_score = Σ (sub_score × weight)`
