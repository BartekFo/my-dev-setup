# IT Innovation Tracker — JSON Schema Reference

This file defines the **canonical JSON schema** that acts as the bridge between
data ingestion/classification (Step 1–3) and dashboard rendering (Step 4).

All data processing MUST output this JSON. The dashboard MUST consume this JSON.
This is the single source of truth.

## Schema Version

```
schema_version: "1.0"
```

## Full Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-12-15T10:30:00Z",

  "meta": {
    "title": "IT Portfolio Analysis — Q4 2025",
    "period": "Q4 2025",
    "currency": "USD",
    "metric_type": "cost | effort | hybrid",
    "metric_unit": "$ | hours | SP | FTE | tasks",
    "org_name": "Acme Corp",
    "industry": "financial_services | healthcare | retail | technology | manufacturing | government | telecom | energy | education | media | other",
    "notes": "Optional analyst notes about data quality, assumptions, etc."
  },

  "summary": {
    "total_value": 950000,
    "maintenance_value": 300000,
    "innovation_value": 650000,
    "maintenance_pct": 31.6,
    "innovation_pct": 68.4,
    "item_count": 10,
    "maintenance_count": 6,
    "innovation_count": 4,
    "health_status": "healthy | at_risk | critical",
    "health_label": "Strong innovation investment",
    "flagged_items_count": 2
  },

  "items": [
    {
      "id": "item-001",
      "name": "Server Security Patching",
      "category": "maintenance | innovation",
      "value": 45000,
      "unit": "$",
      "team": "Platform",
      "source_label": "bug",
      "confidence": "high | medium | low",
      "classification_reason": "Matched high-confidence keyword: 'patching'",
      "flagged": false,
      "notes": ""
    }
  ],

  "by_team": [
    {
      "team": "Platform",
      "total_value": 250000,
      "maintenance_value": 170000,
      "innovation_value": 80000,
      "maintenance_pct": 68.0,
      "innovation_pct": 32.0
    }
  ],

  "top_maintenance": [
    { "name": "CRM v12 Upgrade", "value": 80000, "pct_of_total": 8.4 }
  ],

  "top_innovation": [
    { "name": "Customer Mobile App", "value": 200000, "pct_of_total": 21.1 }
  ],

  "history": [
    {
      "period": "Q1 2025",
      "innovation_pct": 28,
      "maintenance_pct": 72,
      "total_value": 800000
    }
  ],

  "recommendations": [
    {
      "type": "positive | warning | critical | trend",
      "icon": "✦ | ⚠ | 🚨 | 📈",
      "text": "Actionable recommendation referencing specific items."
    }
  ],

  "industry_benchmark": {
    "industry": "financial_services",
    "typical_maintenance_pct": 70,
    "typical_innovation_pct": 30,
    "comparison": "above_benchmark | at_benchmark | below_benchmark",
    "comparison_label": "Your innovation ratio is 38 points above your industry average"
  },

  "classification_stats": {
    "auto_classified": 8,
    "user_overridden": 0,
    "flagged_for_review": 2,
    "high_confidence": 7,
    "medium_confidence": 2,
    "low_confidence": 1
  }
}
```

## Field Descriptions

### `meta`
| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Dashboard heading, include period |
| `period` | yes | Time period label (e.g. "Q4 2025", "FY2025", "Jan 2026") |
| `currency` | no | ISO currency code, only if cost-based |
| `metric_type` | yes | `cost`, `effort`, or `hybrid` |
| `metric_unit` | yes | Primary unit: `$`, `hours`, `SP`, `FTE`, `tasks` |
| `org_name` | no | Organization name if provided |
| `industry` | no | Industry for benchmark comparison |
| `notes` | no | Analyst notes about assumptions or data quality |

### `summary`
Pre-computed totals and health assessment. The dashboard reads these directly
for hero metrics — no re-computation needed.

**Health thresholds:**
- `healthy`: innovation_pct > 40
- `at_risk`: innovation_pct 25–40
- `critical`: innovation_pct < 25

### `items`
Each classified work item. Fields:
- `id`: Unique identifier (auto-generated if not in source data)
- `category`: Must be `"maintenance"` or `"innovation"`
- `confidence`: How sure the classifier is (`high`, `medium`, `low`)
- `classification_reason`: Why this classification was chosen (for transparency)
- `flagged`: `true` if the item needs user review (ambiguous classification)
- `source_label`: Original label/type from source data if available

### `by_team`
Per-team breakdown. Only present if team/department data is available in the source.

### `top_maintenance` / `top_innovation`
Pre-sorted top-5 items per category for the bar charts. Includes `pct_of_total`.

### `history`
Historical periods for trend chart. Only present if multi-period data is available.
Sorted chronologically (oldest first).

### `recommendations`
Pre-generated actionable insights. Types:
- `positive`: Things going well
- `warning`: Areas of concern
- `critical`: Urgent issues
- `trend`: Trajectory observation

### `industry_benchmark`
Comparison against industry averages (from `references/industry-benchmarks.md`).
Only present if industry is known.

### `classification_stats`
Transparency metrics about the auto-classification process.

## Generating the JSON

Use `scripts/process_data.py` to generate this JSON from raw inputs:

```bash
python3 scripts/process_data.py \
  --input project_data.csv \
  --financials pl_data.csv \
  --period "Q4 2025" \
  --currency USD \
  --industry financial_services \
  --output tracker_output.json
```

Or generate it inline by constructing the JSON directly when data is provided
in conversation (chat-based input). The script is a convenience for file-based workflows.

## Consuming the JSON

The dashboard React component imports or receives this JSON and renders it directly.
The dashboard should NOT re-compute `summary`, `top_maintenance`, `top_innovation`,
or `recommendations` — these are pre-computed in the JSON so the dashboard stays
a pure rendering layer.

```jsx
// The dashboard component receives the full JSON as a prop
export default function ITInnovationDashboard({ data }) {
  const { meta, summary, items, top_maintenance, top_innovation, history, recommendations } = data;
  // ... render directly from these fields
}
```
