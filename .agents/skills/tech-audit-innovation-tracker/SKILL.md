---
name: tech-audit-innovation-tracker
description: >
  Analyze IT project management data and P&L financials to calculate and visualize the
  split between maintenance work and innovation/new functionality work. Use this skill
  whenever the user mentions maintenance vs innovation ratio, IT spend analysis, project
  portfolio health, run-the-business vs change-the-business metrics, technical debt
  tracking, capex vs opex IT split, or wants to understand how their engineering effort
  is distributed between keeping-the-lights-on and building new things. Also trigger when
  the user uploads project management exports (Jira, Azure DevOps, Monday.com, Asana,
  Smartsheet, MS Project, CSV/Excel project lists) combined with financial data (P&L
  statements, cost center reports, budget spreadsheets). Even if the user just says
  "show me where our IT money goes" or "how innovative is our IT department" — use this skill.
---

# IT Innovation Tracker

Analyze IT project data and financials to measure the maintenance-vs-innovation split — the
single most important health metric for any IT organization.

## Why This Matters

Organizations that spend >70% on maintenance are in a "keep-the-lights-on trap" — they can't
invest in growth. Best-in-class IT departments target a 60/40 or even 50/50 split between
maintenance and innovation. This skill gives leaders the hard numbers to drive that conversation.

## Architecture: JSON-First Pipeline

The skill follows a strict two-phase architecture:

```
  Raw Data (CSV/XLSX/JSON/chat)
          │
          ▼
  ┌─────────────────────┐
  │  Phase 1: PROCESS   │  → scripts/process_data.py or inline logic
  │  Ingest + Classify  │
  │  + Compute Metrics  │
  └────────┬────────────┘
           │
           ▼
    tracker_output.json    ← Canonical JSON (see references/json-schema.md)
           │
           ▼
  ┌─────────────────────┐
  │  Phase 2: REVIEW    │  → Manually review each json item with "No keyword match - defaulting to maintenance (conservative)" classification reason and add note with suggestion on classification.
  │  Classification     │
  │  No re-computation  │
  └─────────────────────┘
           │
           ▼
    reviewed_tracker_output.json    ← Canonical JSON (see references/json-schema.md)
           │
           ▼
  ┌─────────────────────┐
  │  Phase 3: RENDER    │  → React dashboard artifact
  │  Pure visualization │
  │  No re-computation  │
  └─────────────────────┘

```

The JSON is the **contract** between data processing and visualization. The dashboard
is a pure rendering layer — it reads the JSON and displays it, no re-computation.

Read `references/json-schema.md` for the full schema specification before generating any output.

## Phase 1 — Process Data

### Step 1: Ingest

Accept data in any of these forms (be flexible, real-world data is messy):

**Project Management Data** (any of):
- Jira/Azure DevOps export (CSV, JSON, Excel)
- Spreadsheet with project/task list
- Monday.com, Asana, Smartsheet exports
- Manual list described by user in chat
- Screenshots of dashboards (extract what you can)

**Financial Data** (any of):
- P&L statement (PDF, Excel, CSV)
- Budget/cost center spreadsheet
- Manual figures shared in chat
- Invoice/billing summaries

If the user provides only one type, ask for the other. If they can't provide financials,
fall back to effort-based analysis (hours/story points/task count) and note that the
output reflects effort allocation, not cost allocation.

### Step 2: Classify

Every project, task, epic, or line item must be classified into one of two buckets:

| Category | Also Known As | Examples |
|----------|--------------|----------|
| **Maintenance** | Run-the-business, BAU, keep-the-lights-on, sustain, support | Bug fixes, patching, upgrades, compliance, infra maintenance, incident response, tech debt remediation, license renewals, security updates, monitoring, backup |
| **Innovation** | Change-the-business, growth, transformation, new capability | New features, new products, new integrations, process automation, platform migration (strategic), R&D, PoCs, new market capabilities, UX redesigns, AI/ML initiatives |

**Classification approach:**
1. Use explicit labels first — if the data has tags like "bug", "enhancement", "maintenance", use them
2. Match project/epic names against keyword lists (see `references/classification-keywords.md`)
3. If a project is mixed, ask the user or split proportionally
4. When in doubt, classify as maintenance (conservative — it's the harder truth)
5. Flag low-confidence items with `"flagged": true` for user review

### Step 3: Compute & Output JSON

**For file-based input**, run the processing script:

```bash
python3 scripts/process_data.py \
  --input project_data.csv \
  --period "Q4 2025" \
  --currency USD \
  --industry technology \
  --output tracker_output.json
```

Script options:
- `--input FILE` — project data (CSV, XLSX, JSON) **(required)**
- `--financials FILE` — optional P&L data
- `--sheet NAME` — sheet name for Excel files
- `--period TEXT` — period label (default: "Current")
- `--currency CODE` — ISO currency (default: USD)
- `--metric-type` — cost | effort | hybrid
- `--metric-unit` — $ | hours | SP | FTE | tasks
- `--industry` — for benchmark comparison
- `--org-name` — organization name
- `--history FILE` — historical JSON for trend data
- `--output FILE` — output path (default: tracker_output.json)

**For chat-based input** (user gives data in conversation), construct the JSON inline
following the schema in `references/json-schema.md`. Compute all fields: summary totals,
percentages, health status, top lists, recommendations, and benchmarks.

The JSON MUST include all required sections: `meta`, `summary`, `items`,
`top_maintenance`, `top_innovation`, `recommendations`, `industry_benchmark`,
and `classification_stats`. Optional: `by_team`, `history`.

### Step 4: Save JSON output

Always save the generated JSON as a file the user can download. This is the
reusable data artifact — they can feed it into other tools, track changes over time,
or re-render with different dashboards.

## Phase 2 — Review

Using Phase 1, Step 2 approach review the classification output.
Your classification review notes on the specific item should be added to notes field.
Always save the generated JSON as a new file the user can download. This is the
reusable data artifact — they can feed it into other tools, track changes over time,
or re-render with different dashboards.

## Phase 3 — Render Dashboard

Create a **single-file React (.jsx) artifact** that reads the JSON and visualizes it.

Read `references/dashboard-spec.md` for the full design specification.

The dashboard component receives the full JSON as embedded data and renders:

1. **Hero metric** — the big numbers: "X% Innovation | Y% Maintenance"
2. **Donut/ring chart** — visual split with color coding
3. **Trend line** — if `history` has 2+ periods
4. **Top drivers** — horizontal bar charts from `top_maintenance` / `top_innovation`
5. **Breakdown table** — all `items`, sortable, with category badges
6. **Health indicator** — from `summary.health_status`
7. **Industry benchmark** — from `industry_benchmark.comparison_label`
8. **Recommendations** — from `recommendations` array
9. **Classification confidence** — from `classification_stats`

The dashboard MUST read directly from the JSON fields. It MUST NOT re-compute
summary values, percentages, or recommendations.

Design: Executive-grade analytics. Dark theme. Bloomberg meets modern SaaS.
Use the frontend-design skill principles for visual quality.

## Phase 3 — Present & Interpret

After generating both outputs, provide:
1. A brief executive summary (2-3 sentences)
2. The key finding — is the ratio healthy?
3. One specific, actionable recommendation
4. Caveats about classification assumptions made
5. Links to both files: the JSON and the dashboard

## Edge Cases

- **No financial data**: Use effort metrics, set `metric_type: "effort"` in JSON
- **Single project**: Break down by tasks/stories within the project
- **User disagrees with classification**: Override in JSON, set `"user_overridden"` count, re-render
- **Ambiguous items**: Flag with `"flagged": true`, ask user, default to maintenance
- **Historical comparison**: Populate `history` array, dashboard shows trend automatically
- **Multiple currencies**: Normalize to one, note conversion in `meta.notes`

## Output Files

1. **`tracker_output.json`** — the canonical data file (Phase 1 output)
2. **React dashboard artifact** (.jsx) — the visualization (Phase 2 output)
3. **Executive summary** — brief text interpretation (Phase 3)

## References

- `references/json-schema.md` — **READ FIRST** — the canonical JSON schema (contract)
- `references/classification-keywords.md` — keyword lists for auto-classification
- `references/dashboard-spec.md` — detailed dashboard design specification
- `references/industry-benchmarks.md` — reference ratios by industry
