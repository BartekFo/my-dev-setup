---
name: tech-audit-code-review
description: >
  Analyze a code repository and produce an engineering health dashboard with five key metrics:
  Vulnerability Density (critical vulns per KLOC), Change Failure Rate (CFR), DORA Lead Time
  for Changes, Technical Debt Ratio (TDR), and Automated Test Coverage. Use this skill whenever
  the user asks to review a codebase, audit repository health, generate engineering metrics,
  assess code quality, produce a DevOps dashboard, measure technical debt, check test coverage,
  evaluate deployment stability, or wants any kind of code health report or engineering KPI
  overview — even if they don't use the exact metric names. Also trigger when the user uploads
  or points to a repository and says things like "how healthy is this repo", "give me a quality
  report", "what's the state of this codebase", or "score this project".
---

# Code Review Dashboard

Analyze a code repository and render an engineering-health dashboard backed by five standardized
metrics. Every metric is computed (or estimated from heuristics when full CI/CD data is
unavailable) and serialized to a canonical JSON structure **before** the dashboard is rendered.

## When to use

Trigger this skill when the user wants insight into the quality, stability, or maintainability
of a codebase. Common phrasings include "review this repo", "code health check", "engineering
metrics", "technical debt report", "how's my codebase doing", etc.

## Important
Use serena tool whenever you need to navigate or search files.

---

## Workflow

### 1. Locate the repository

Identify the repo the user wants analyzed. It may be:

- A local path (e.g., `/home/user/project` or an uploaded archive)
- A GitHub URL (clone it first)
- Already present in the working directory

If the repo is an archive (`.zip`, `.tar.gz`), extract it first.

### 2. Run the analysis script

If directory under `<repo-root>/tech-audit-code-review` does not exist, create it.
Execute the bundled analysis script against the repo root if file under `<repo-root>/tech-audit-code-review/metrics.json` does not exist:

```bash
python <skill-path>/scripts/analyze_repo.py <repo-root> --output <repo-root>/tech-audit-code-review/metrics.json
```

The script performs static analysis across five dimensions and writes a single JSON file
containing all metric results. Read `references/metrics-spec.md` for the detailed definition
of each metric, how it is computed, and what the score bands mean.

**Important**: the script is designed to work with *zero* external services. It derives
metrics from the repository contents alone (source code, git history, config files, test
files). When real CI/CD or vulnerability-scanner data is unavailable it applies documented
heuristics — and flags each metric with a `confidence` field (`high`, `medium`, or `low`)
so the dashboard can communicate uncertainty honestly.

### 3. Review the JSON output

Before rendering, read `metrics.json` and sanity-check it. The schema is:

```json
{
  "repository": "<name>",
  "analyzed_at": "<ISO-8601>",
  "summary_score": 0-100,
  "metrics": {
    "vulnerability_density": { "value": ..., "unit": "per_kloc", "rating": "...", "confidence": "...", "details": {...} },
    "change_failure_rate":   { "value": ..., "unit": "percent",  "rating": "...", "confidence": "...", "details": {...} },
    "lead_time_for_changes": { "value": ..., "unit": "hours",    "rating": "...", "confidence": "...", "details": {...} },
    "technical_debt_ratio":  { "value": ..., "unit": "percent",  "rating": "...", "confidence": "...", "details": {...} },
    "test_coverage":         { "value": ..., "unit": "percent",  "rating": "...", "confidence": "...", "details": {...} }
  }
}
```

Each `rating` is one of: `elite`, `good`, `fair`, `poor`.

### 4. Render the dashboard

Generate a single-file HTML dashboard (React/JSX artifact) that:

- Loads the JSON inline (embed it as a JS constant)
- Displays all five metrics as visual cards with gauges or progress indicators
- Uses the `rating` field to drive color coding (elite=green, good=blue, fair=amber, poor=red)
- Shows the `confidence` badge on each card so the user knows which numbers are solid vs estimated
- Includes a summary score ring at the top
- Has a collapsible "Details" panel per metric with the underlying data
- Follows the frontend-design skill principles: bold aesthetic, distinctive typography,
  cohesive color palette, and thoughtful motion.

### 5. Present results

Save the dashboard in place where skill was executed under `<repo-root>/tech-audit-code-review/outputs/` and present it with `present_files`.
Also save the raw `metrics.json` so the user can integrate the data elsewhere.

---

## Metric Definitions (quick reference)

For full computation logic see `references/metrics-spec.md`.

| Metric | What it measures | Elite | Good | Fair | Poor |
|---|---|---|---|---|---|
| **Vulnerability Density** | Critical security issues per 1,000 lines of code | 0 | < 0.5 | < 2 | ≥ 2 |
| **Change Failure Rate** | % of changes (merges) that were reverted or immediately fixed | < 5% | < 10% | < 20% | ≥ 20% |
| **Lead Time for Changes** | Median hours from first commit on a branch to merge | < 24h | < 72h | < 168h | ≥ 168h |
| **Technical Debt Ratio** | Estimated remediation cost as % of total development effort | < 5% | < 10% | < 20% | ≥ 20% |
| **Test Coverage** | Weighted blend of test-file ratio + business-path heuristic | > 80% | > 60% | > 40% | ≤ 40% |

---

## Important notes

- **Honesty over impressiveness.** If the repo lacks git history, say so — don't fabricate
  DORA or CFR numbers. The `confidence` field exists for this purpose.
- **Language agnostic.** The analysis script detects the dominant language(s) and adapts its
  heuristics (e.g., test file naming conventions differ between Python, JS, Java, Go, etc.).
- **No network required.** Everything runs locally against the repo contents.

## References

- `references/metrics-spec.md` — specification of metrics, outputs, and reasoning
- `references/dashboard-spec.md` — detailed dashboard design specification
