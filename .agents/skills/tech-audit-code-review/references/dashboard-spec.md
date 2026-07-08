# Dashboard Design Specification

## Design Direction

The Engineering Health Dashboard is designed as a professional code analytics platform —
clean, developer-focused, and data-driven. Think GitHub Insights meets developer
observability platforms like DataDog or New Relic.

### Color Palette
- **Background**: Deep slate gradient (`linear-gradient(135deg, #0f172a 0%, #1e293b 100%)`)
- **Surface**: Elevated cards (`linear-gradient(135deg, #1e293b 0%, #334155 100%)`)
- **Elite rating**: Vibrant green (`#10b981`, `#34d399`)
- **Good rating**: Blue (`#3b82f6`, `#60a5fa`)
- **Fair rating**: Amber/orange (`#f59e0b`, `#fbbf24`)
- **Poor rating**: Red (`#ef4444`, `#f87171`)
- **Text primary**: Light slate (`#e2e8f0`, `#f1f5f9`)
- **Text secondary**: Muted slate (`#94a3b8`)
- **Text tertiary**: Dark slate (`#64748b`)
- **Accent borders**: Subtle white overlay (`rgba(255,255,255,0.1)`)
- **Surface overlays**: Black transparency (`rgba(0,0,0,0.2)` - `rgba(0,0,0,0.4)`)

### Typography
- **Font Stack**: `-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif`
- **Display/headers**: 3rem (48px), weight 800, gradient text effect
- **Section headers**: 1.5rem (24px), weight 700
- **Metric titles**: 1.125rem (18px), weight 700
- **Metric values**: 3rem (48px), weight 800
- **Body text**: 0.875rem (14px)
- **Code/monospace**: Monaco, Consolas, monospace (for file paths)

### Layout Structure

```
┌───────────────────────────────────────────────────────────────┐
│                 Engineering Health Dashboard                  │
│                      lrc-pos                                  │
│               Analyzed: [timestamp]                           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  SUMMARY CARD                                          │   │
│  │  ┌──────────┐  Repository Summary                      │   │
│  │  │          │  ┌────────────┬────────────┐             │   │
│  │  │  SCORE   │  │ 1 Elite    │ 1 Good     │             │   │
│  │  │  RING    │  │ Outstanding│ Solid      │             │   │
│  │  │  48.8    │  ├────────────┼────────────┤             │   │
│  │  │          │  │ 0 Fair     │ 3 Poor     │             │   │
│  │  └──────────┘  │ Needs Work │ Action Req │             │   │
│  │                └────────────┴────────────┘             │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │Recommendations                                   │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ 🔒 VULN        │ │ ⚠️ CHANGE       │ │ ⚡ LEAD TIME     │    │
│  │ DENSITY        │ │ FAILURE RATE    │ │ FOR CHANGES     │   │
│  │                │ │                 │ │                 │   │
│  │ [GOOD]         │ │ [POOR]          │ │ [ELITE]         │   │
│  │ HIGH CONF      │ │ MEDIUM CONF     │ │ MEDIUM CONF     │   │
│  │                │ │                 │ │                 │   │
│  │ 0.3 /KLOC      │ │ 107.7 %         │ │ 0.3 hours       │   │
│  │ ▓▓▓▓░░░░       │ │ ▓▓▓▓░░░░        │ │ ▓▓▓▓▓▓▓▓        │   │
│  │                │ │                 │ │                 │   │
│  │ ▼ Show Details │ │ ▼ Show Details  │ │ ▼ Show Details  │   │
│  └────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                               │
│  ┌─────────────────┐ ┌─────────────────┐                      │
│  │ 🏗️ TECH DEBT    │ │ ✅ TEST         │                      │
│  │ RATIO           │ │ COVERAGE        │                      │
│  │                 │ │                 │                      │
│  │ [POOR]          │ │ [POOR]          │                      │
│  │ HIGH CONF       │ │ MEDIUM CONF     │                      │
│  │                 │ │                 │                      │
│  │ 279.6 %         │ │ 34.5 %          │                      │
│  │ ▓▓▓░░░░░        │ │ ▓▓░░░░░░        │                      │
│  │                 │ │                 │                      │
│  │ ▼ Show Details  │ │ ▼ Show Details  │                      │
│  └─────────────────┘ └─────────────────┘                      │
└───────────────────────────────────────────────────────────────┘
```

## Component Specifications

### Header Section
- **Title**: 3rem, weight 800, gradient text (blue to purple: `#60a5fa` to `#a78bfa`)
- **Repository name**: 1.25rem, medium slate color (`#94a3b8`), weight 500
- **Timestamp**: 0.875rem, dark slate (`#64748b`), displays formatted local time
- **Alignment**: Center
- **Margin**: 3rem bottom spacing

### Summary Card
- **Layout**: Horizontal flexbox with centered alignment, 3rem gap
- **Background**: Gradient card with elevated surface
- **Border radius**: 1.5rem
- **Padding**: 2rem
- **Shadow**: Deep shadow (`0 20px 60px rgba(0,0,0,0.4)`)
- **Border**: Subtle white overlay

#### Score Ring Component
- **Type**: SVG circular progress indicator
- **Dimensions**: 180x180px
- **Ring radius**: 75px, stroke width 12px
- **Colors**: Dynamic based on score:
  - ≥80: Green (`#10b981`)
  - 60-79: Blue (`#3b82f6`)
  - 40-59: Amber (`#f59e0b`)
  - <40: Red (`#ef4444`)
- **Animation**: Stroke-dashoffset transition (1s ease)
- **Center label**: Score value (3rem, weight 800) + "Overall Score" text

#### Repository Summary Stats
- **Layout**: 2x2 grid, 1rem gap
- **Stat icons**: 40x40px rounded containers with category color background (20% opacity)
- **Counter display**: Large bold number (Elite/Good/Fair/Poor count)
- **Labels**: Small descriptive text + status label

### Metric Cards
- **Layout**: Responsive grid (`repeat(auto-fit, minmax(400px, 1fr))`)
- **Gap**: 1.5rem
- **Background**: Same gradient as summary card
- **Border radius**: 1.25rem
- **Padding**: 1.75rem
- **Hover effect**: Translate up 4px + enhanced shadow
- **Staggered animation**: Fade in from bottom (0.6s) with 0.1s delays
- **Details section**: Each metric card MUST contain details section based on details key in json output.

#### Metric Header
- **Icon + Title**: Emoji icon, 1.125rem title, weight 700
- **Description**: Small text (0.875rem) explaining the metric
- **Badges**: Right-aligned pills
  - **Rating badge**: Color-coded (Elite/Good/Fair/Poor)
  - **Confidence badge**: Grayscale (High/Medium/Low)
  - **Style**: 0.25rem vertical, 0.75rem horizontal padding, uppercase, letter-spacing 0.5px

#### Metric Value Display
- **Size**: 3rem, weight 800
- **Color**: Dynamic based on rating
- **Unit suffix**: 1.5rem, 70% opacity, margin-left 0.5rem
- **Units**: `/KLOC`, `%`, `hours`, `percent`

#### Progress Bar
- **Height**: 8px
- **Background**: Dark slate (`#334155`)
- **Border radius**: Full round (999px)
- **Fill**: Gradient based on rating
  - Elite: Green gradient (`#10b981` to `#34d399`)
  - Good: Blue gradient (`#3b82f6` to `#60a5fa`)
  - Fair: Amber gradient (`#f59e0b` to `#fbbf24`)
  - Poor: Red gradient (`#ef4444` to `#f87171`)
- **Width calculation**:
  - For percentage metrics: min(100, value)%
  - For rated metrics: Elite 100%, Good 75%, Fair 50%, Poor 25%
- **Animation**: Width transition (1s ease)

#### Details Toggle Button
- **Style**: Borderless with subtle border (`rgba(255,255,255,0.1)`)
- **Padding**: 0.5rem 1rem
- **Border radius**: 0.5rem
- **Width**: 100%
- **Hover**: Background overlay + brighter border + lighter text
- **Icons**: ▼ collapsed, ▲ expanded
- **Action**: Clickable, expends Details Panel

#### Details Panel (Expandable)
- **Margin**: 1rem top
- **Padding**: 1rem top
- **Border**: Top border with subtle white overlay
- **Content varies by metric type**
- **Details section**: Each metric card MUST contain details section based on details key in json output.

##### Vulnerability Density Details
1. **Code Statistics**: LOC, total findings, weighted score
2. **Finding Categories**: Breakdown by category (hardcoded_secret, dangerous_function, etc.)
3. **Top Security Findings List**:
   - Max height: 300px with scroll
   - Individual finding cards with dark background overlay
   - Header: File path (blue, monospace) + Type badge (red pill)
   - Detail text in light slate

##### Change Failure Rate Details
1. **Analysis Period**: Time window description
2. **Merge Statistics**: Total merges, reverts, hotfixes counts
3. **Failure Commits**: Bulleted list (showing first 10, truncated with count if more)

##### Lead Time for Changes Details
1. **Analysis Period**: Time window description
2. **Timing Statistics**: Merge count, median, p90, shortest, longest (all in hours with 1 decimal)

##### Technical Debt Ratio Details
1. **Overall Statistics**: Total issues, remediation time (hours), development time (hours)
2. **Issue Breakdown**: Categorized counts (long_functions, long_files, todo_comments, deep_nesting, duplicated_blocks)

##### Test Coverage Details
1. **Test Statistics**: Test files count, test LOC, source LOC, test ratio percentage
2. **Business Paths Covered**: Color-coded checkmarks (green ✓ covered, red ✗ not covered)
   - Paths: auth, payment, validation, error_handling, api_endpoints
3. **Score Components**: Business path score, structural score, composite score

## Animation Guidelines

### Entrance Animations
- **Metric cards**: `fadeIn` animation (0.6s ease forwards)
  - From: opacity 0, translateY(20px)
  - To: opacity 1, translateY(0)
  - Stagger: 0.1s delay per card (nth-child)

### Interactive Animations
- **Score ring**: Stroke-dashoffset transition (1s ease) on load
- **Progress bars**: Width transition (1s ease) on render
- **Card hover**: Transform translateY(-4px) + shadow enhancement (0.2s)
- **Button hover**: Background, border, color transitions (0.2s)

### Timing
- Page load: Cards appear sequentially with 100ms stagger
- Initial opacity: 0 for cards, set via nth-child animation delays
- All transitions: 0.2s - 1s depending on element

## Responsive Behavior

- **Desktop (1400px max-width)**: Full grid layout as specified
- **Grid behavior**: `auto-fit` with `minmax(400px, 1fr)` ensures responsive wrapping
- **Cards**: Maintain minimum 400px width, stack when viewport narrows
- **Summary card**: Flexbox with gap, wraps naturally on smaller screens

## Data Format Expected

The dashboard component expects a `METRICS_DATA` object with this structure:

```javascript
const METRICS_DATA = {
  repository: "repository-name",
  analyzed_at: "2026-02-27T12:54:14.244054+00:00",  // ISO 8601 timestamp
  summary_score: 48.8,  // Overall health score (0-100)

  metrics: {
    vulnerability_density: {
      value: 0.282,
      unit: "per_kloc",
      rating: "elite" | "good" | "fair" | "poor",
      confidence: "high" | "medium" | "low",
      details: {
        loc: 63821,
        kloc: 63.821,
        findings_count: 8,
        weighted_score: 18,
        categories: {
          hardcoded_secret: 2,
          dangerous_function: 6
        },
        top_findings: [
          {
            file: "firebase-test.js",
            line: 7,
            type: "hardcoded_secret",
            detail: "Potential hardcoded secret/credential",
            weight: 3
          }
          // ... more findings
        ]
      }
    },

    change_failure_rate: {
      value: 107.7,
      unit: "percent",
      rating: "elite" | "good" | "fair" | "poor",
      confidence: "high" | "medium" | "low",
      details: {
        total_merges: 13,
        reverts: 1,
        hotfixes: 13,
        failure_commits: ["90c0b5d", "960cc98", ...],
        analysis_window: "last 6 months"
      }
    },

    lead_time_for_changes: {
      value: 0.3,
      unit: "hours",
      rating: "elite" | "good" | "fair" | "poor",
      confidence: "high" | "medium" | "low",
      details: {
        merge_count: 13,
        median_hours: 0.3,
        p90_hours: 514.4,
        shortest_hours: 0.0,
        longest_hours: 790.7,
        analysis_window: "last 6 months"
      }
    },

    technical_debt_ratio: {
      value: 279.6,
      unit: "percent",
      rating: "elite" | "good" | "fair" | "poor",
      confidence: "high" | "medium" | "low",
      details: {
        total_issues: 5749,
        remediation_minutes: 89230,
        development_minutes: 31910,
        breakdown: {
          long_functions: 102,
          long_files: 31,
          todo_comments: 6,
          deep_nesting: 20,
          duplicated_blocks: 5590
        }
      }
    },

    test_coverage: {
      value: 34.5,
      unit: "percent",
      rating: "elite" | "good" | "fair" | "poor",
      confidence: "high" | "medium" | "low",
      details: {
        test_files: 16,
        test_loc: 803,
        source_loc: 63821,
        test_ratio: 0.013,
        business_paths: {
          auth: true,
          payment: false,
          validation: true,
          error_handling: true,
          api_endpoints: true
        },
        business_path_score: 80,
        structural_score: 4.2,
        composite_score: 34.5
      }
    }
  }
};
```

## Metric Definitions

### 1. Vulnerability Density
**Unit**: Critical security issues per 1,000 lines of code
**Description**: Measures security risk by counting hardcoded secrets, dangerous function usage, and other vulnerability patterns
**Icon**: 🔒

### 2. Change Failure Rate (CFR)
**Unit**: Percentage
**Description**: % of changes that were reverted or immediately fixed (hotfixes). Derived from DORA metrics
**Icon**: ⚠️

### 3. Lead Time for Changes
**Unit**: Hours
**Description**: Median time from first commit to merge. Part of DORA metrics for deployment velocity
**Icon**: ⚡

### 4. Technical Debt Ratio (TDR)
**Unit**: Percentage
**Description**: Estimated remediation cost as % of development effort. Based on code complexity, duplication, and maintainability issues
**Icon**: 🏗️

### 5. Test Coverage
**Unit**: Percentage
**Description**: Weighted blend of test-file ratio + business-path heuristic. Not a traditional code coverage metric
**Icon**: ✅

## Rating Scale

All metrics use a 4-tier rating system:

- **Elite**: Industry-leading performance
- **Good**: Above average, solid performance
- **Fair**: Adequate but with room for improvement
- **Poor**: Below standard, action required

## Confidence Levels

Each metric includes a confidence indicator:

- **High**: Based on complete data with strong signals
- **Medium**: Based on partial data or heuristics
- **Low**: Based on limited data or estimates

## Implementation Notes

### Technology Stack
- **React**: 18.x (loaded via CDN)
- **Babel Standalone**: For JSX transformation in browser
- **No build step**: Self-contained HTML file
- **State management**: React.useState for expandable sections

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS features: Grid, Flexbox, CSS custom properties, gradients, transforms
- SVG support required for score ring

### Performance Considerations
- Single page application with no routing
- All data embedded in JavaScript constant
- Minimal re-renders (toggle state only affects individual cards)
- CSS animations use transform and opacity for GPU acceleration
