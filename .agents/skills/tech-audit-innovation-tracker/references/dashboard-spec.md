# Dashboard Design Specification

## Design Direction

The dashboard should feel like an executive-grade analytics tool — confident, data-forward,
and visually striking. Think Bloomberg terminal meets modern SaaS analytics.
Dashboard NEEDS TO BE an html file.
Utilize recarts from https://cdnjs.cloudflare.com/ajax/libs/recharts/3.2.1/Recharts.min.js url.

### Color Palette
- **Background**: Deep charcoal/navy (`#0F1419` or `#111827`)
- **Surface**: Slightly lighter (`#1A1F2E` or `#1F2937`)
- **Innovation color**: Electric teal/cyan (`#06D6A0` or `#00E5A0`)
- **Maintenance color**: Warm amber/orange (`#FF6B35` or `#F59E0B`)
- **Danger/warning**: Coral red (`#EF4444`)
- **Text primary**: Near-white (`#F9FAFB`)
- **Text secondary**: Muted (`#9CA3AF`)
- **Accent borders**: Subtle (`rgba(255,255,255,0.06)`)

### Typography
Use Google Fonts. Suggestions (vary these — don't always use the same):
- Display/headers: JetBrains Mono, Space Grotesk, DM Sans, Outfit, Plus Jakarta Sans
- Numbers/metrics: JetBrains Mono, IBM Plex Mono, Source Code Pro
- Body: Inter, DM Sans, Plus Jakarta Sans

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  IT Innovation Tracker                    [period selector] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │                  │  │                            │   │
│  │   DONUT CHART    │  │    HERO METRICS            │   │
│  │   Innovation %   │  │    Innovation: XX%         │   │
│  │   Maintenance %  │  │    Maintenance: XX%        │   │
│  │                  │  │    Health: [indicator]      │   │
│  └──────────────────┘  └────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │   TREND LINE (if multi-period)                    │   │
│  │   Shows innovation % over time                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────┐ ┌────────────────────────┐  │
│  │  TOP MAINTENANCE       │ │  TOP INNOVATION        │  │
│  │  COST DRIVERS          │ │  INVESTMENTS           │  │
│  │  1. ████████ $XXk      │ │  1. ████████ $XXk      │  │
│  │  2. ██████   $XXk      │ │  2. ██████   $XXk      │  │
│  │  3. ████     $XXk      │ │  3. ████     $XXk      │  │
│  └────────────────────────┘ └────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  DETAILED BREAKDOWN TABLE                         │   │
│  │  Project | Category | Cost/Effort | % of Total    │   │
│  │  ─────────────────────────────────────────────    │   │
│  │  [sortable, filterable]                           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RECOMMENDATIONS & INSIGHTS                       │   │
│  │  Based on the analysis, actionable suggestions    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Component Specifications

### Hero Metric
- The two percentages should be LARGE (48-72px font)
- Use the category colors for each number
- Include a subtle animation on load (count-up effect)
- Health indicator: colored dot + label (Healthy / At Risk / Critical)

### Donut Chart
- Use recharts PieChart with inner radius for donut effect
- Two segments only (maintenance + innovation)
- Center label showing the dominant category
- Smooth hover effects showing exact values
- Custom tooltip with formatted numbers

### Trend Line
- Only show if data spans 2+ time periods
- Use recharts AreaChart with gradient fill
- Innovation % as the primary line
- Include a reference line at 40% (industry target)
- Subtle grid lines, no visual clutter

### Bar Charts (Top Drivers)
- Horizontal bars, sorted by value
- Top 5 items max per category
- Color-coded by category
- Show value labels at bar ends
- Use recharts BarChart

### Breakdown Table
- Sortable columns
- Category column with colored badge/pill
- Alternating row colors (subtle)
- Right-aligned numbers with proper formatting ($, %, commas)
- Search/filter capability if >10 items

### Health Assessment
The health score is based on innovation percentage:
- **>40% innovation** → 🟢 Healthy — "Strong innovation investment"
- **25-40% innovation** → 🟡 At Risk — "Below target, room for improvement"
- **<25% innovation** → 🔴 Critical — "Maintenance-heavy, innovation starved"

### Recommendations Engine
Based on the data, generate 2-3 actionable recommendations:
- If maintenance-heavy: suggest specific items to automate/eliminate/outsource
- If innovation-heavy: validate that maintenance isn't being neglected
- If trending down: flag the trajectory and suggest course correction
- Always reference specific line items from the data

## Animation Guidelines
- Stagger card appearances (100ms delay each)
- Count-up animation for hero numbers (1.5s ease-out)
- Smooth transitions on hover states
- Chart animations on mount (recharts built-in)

## Responsive Behavior
- Desktop: Full layout as specified
- Tablet: Stack the donut and hero metrics vertically
- Mobile: Single column, all cards stacked

## Data Format Expected

The dashboard component should accept a `data` prop with this shape:

```javascript
const data = {
  title: "IT Portfolio Analysis — Q4 2025",
  period: "Q4 2025",
  currency: "USD",
  metric_type: "cost", // or "effort" or "hybrid"
  items: [
    {
      name: "Project Name",
      category: "maintenance" | "innovation",
      value: 150000,        // cost or effort number
      unit: "$" | "hours" | "SP" | "FTE",
      team: "Platform",     // optional
      confidence: "high" | "medium" | "low",  // classification confidence
      notes: "..."          // optional
    }
  ],
  // Optional: historical data for trends
  history: [
    { period: "Q1 2025", innovation_pct: 28, maintenance_pct: 72 },
    { period: "Q2 2025", innovation_pct: 32, maintenance_pct: 68 },
  ]
};
```
