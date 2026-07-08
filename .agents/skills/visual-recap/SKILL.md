---
name: visual-recap
description: >-
  Turn a PR, branch, commit, or git diff into an interactive visual recap
  delivered as a single local self-contained HTML file — inline diagrams, file
  maps, API/schema summaries, annotated diffs, and focused review notes — that
  opens in a browser so a reviewer sees the shape of the change before the raw
  lines.
metadata:
  visibility: exported
---

# Visual Recap

A visual recap is a structured, scannable review document built **from** a diff,
not toward one. It is the reverse of forward planning: instead of describing the
change you are about to make, you describe the change that was just made, at a
higher altitude than line-by-line review. Schema, API, file, and architecture
changes become the same `pb-data-model`, `pb-api`, `pb-file-tree`, and
`pb-diagram` blocks a forward plan would use, only now they summarize work that
already exists. A reviewer scans the shape of the change before spending
attention on the literal lines.

The recap is one HTML file with zero network dependencies — no CDN, no external
fonts, no third-party scripts, nothing fetched at runtime. Everything (the
design system, diagrams, and interactivity) is inlined so the file opens and
works offline straight from disk.

`/visual-recap` is the packaged command and main entry point. It gathers the
change locally with plain git — `git diff`, `git log`, `git show`,
`git diff --stat` — and renders it into the review surface. No network tools, no
hosted service, no external helpers.

## When To Use

Build a recap when a PR, branch, or commit is large, multi-file, or touches
schema, API contracts, or architecture, and a reviewer would benefit from seeing
the change mapped to structured blocks before reading the raw diff. Generate one
on request — "recap this PR", "show me what this branch changed", "walk me
through what we just built". Skip it for small, single-file, or obvious diffs — a
recap is review overhead, and a tiny change reviews faster as plain diff.

## Recap Discipline

- **Gate thoughtfully.** A recap is a richer review surface, not a receipt for
  every change. Build one when the reviewer needs to see, compare, and reason
  about the shape of a non-trivial change before reading the diff. Skip it for a
  truly trivial, unambiguous diff you could describe in one sentence. Never pad a
  recap with filler and never ship a one-block recap of a large change.
- **Ground everything in the real diff.** Read the actual changed lines first —
  real paths, real fields, real method/path, real before/after text. Reuse-read:
  before you write a block, know which existing file, action, schema, or
  component the change touches, so the recap explains the genuine delta instead
  of redescribing the whole file. The structured blocks are true by construction
  only if they are extracted mechanically from the diff (see "Grounding Rule").
- **Recap is read-only.** Building a recap makes no source edits. The one
  exception is a small local fix strictly needed to make the recap file open (a
  path, a link) — never a change to the code being recapped.
- **Clarify vs. assume.** Do not ask the user to hand-feed the diff — collect it
  locally with git. Ask a concise question only when the scope of the change is
  genuinely ambiguous and cannot be inferred from the diff plus conversation
  context; otherwise state the assumption explicitly in prose and proceed. Keep
  anything genuinely open in the single bottom `pb-open-questions` block.
- **The recap is the review artifact.** After surfacing it, point the reviewer at
  the file and let them read; the recap itself is the handoff, not a separate
  "does this look right?" question. When feedback lands, update the HTML file so
  it still stands alone, rather than only answering in chat.

## The Deliverable Is A Local HTML File — Never Raw Chat

The deliverable is ALWAYS a generated self-contained HTML file, never a chat-only
recap. Do not hand the recap over as inline chat content — no Markdown prose,
ASCII sketch, table, fenced "wireframe", or a "here's what changed" summary
standing in for it. A recap's whole value is the scannable, structured,
interactive document; an inline summary is not a degraded recap, it is the thing
a recap replaces. Build the review document, render it to
`plans/<slug>/recap.html` (or a private scratch location), and hand over the file
path. The chat message points at the file; it never *is* the recap.

Author the file by copying `references/plan-template.html` and filling its
`<main>` with blocks from `references/blocks.md` — do not hand-roll a fresh
document skeleton or invent block markup from memory. The template carries the
whole design system (inline `<style>` tokens for light/dark/print) and a small
vanilla inline `<script>` (collapsible sections, tab switching, copy-code, theme
toggle persisted in `localStorage`), so the file stays fully offline and
self-contained. Never add a `<link>` to a CDN, an external font, a Mermaid
runtime, or any `fetch`/XHR — every asset lives inline.

## Core Workflow

1. **Collect the diff locally.** Gather the change with plain git and nothing
   else: `git diff <base>...<head>` (or `git diff` for the working tree),
   `git diff --stat` for the file footprint, `git log <range>` for the commit
   narrative, and `git show <sha>` for a single commit. Read the real changed
   files where the diff alone is not enough to explain intent. Delegate a wide
   read of a big diff to a sub-agent. Use no network tools at any point.
2. **Choose the visual surface.** Decide document-only vs. a top canvas of
   wireframes before you compose; the Visual Surface Choice section owns the
   rule. Do not add visual chrome to a backend/schema-only recap.
3. **Compose the file.** Copy `references/plan-template.html` and fill its
   `<main>` with blocks from `references/blocks.md`, mapping each kind of change
   to its block per "Diff → Block Mapping" — especially `pb-diff`,
   `pb-annotated-code`, `pb-file-tree`, `pb-data-model`, `pb-api`, and
   `pb-diagram`. Render diagrams as inline SVG or CSS box/flow layouts — never
   Mermaid or any runtime loaded from the network. For UI recaps, build the top
   canvas first with before/after wireframes, then the document body below.
4. **Save.** Write the file to `plans/<slug>/recap.html` when it should be
   checked in, or to a repo-ignored / temp location such as
   `/tmp/visual-plans/<slug>/recap.html` when it should stay private scratch.
5. **Hand off.** Open it for the reviewer — on macOS run `open <path>` — and give
   the exact file path in chat. The recap is the handoff; do not ask a separate
   "does this look good?" question. For high-stakes changes (architecture,
   backend, data, migration, multi-file), kick off the self-review pass while the
   reviewer reads instead of blocking handoff on it.
6. **Iterate.** Take feedback from chat, edit the HTML file directly, and re-open
   it. Use no network tools at any point.

## Recap The Whole Work Unit

When `/visual-recap` is invoked in a chat thread after work has already happened,
the default scope is the whole current work unit/thread, not only the most recent
message or fix. Gather the thread-owned changes across the conversation: the
original implementation, later bug fixes, UI follow-ups, tests, changesets, and
any local import/linking fixes needed to make the recap open.

Use the current diff plus conversation context to separate thread-owned changes
from unrelated dirty work that existed before the thread, and exclude the
pre-existing edits. If the scope is genuinely ambiguous and cannot be inferred,
state the assumption or ask a concise question before rendering.

When updating an existing recap after feedback, revise it so it still covers the
whole thread/work unit plus the new correction. Do not replace a broad recap with
a narrow recap of only the latest feedback unless the reviewer explicitly asks
for that narrower scope.

## Keep The Recap Body Lean

Do not add boilerplate intro, disclaimer, provenance, or summary prose to the
recap body. In particular, do not add a `pb-prose` block just to say the recap is
an aid, that the reviewer should still read the diff, how many files changed, or
which ref generated it. The title, the meta row, and the `pb-file-tree` (which
carries the per-file change flags) already carry that context.

Only add prose when it tells the reviewer something specific the structured
blocks do not: the objective, a real compatibility risk, an important decision
visible in the diff, or a grounded review note.

## Recaps Must Be Substantial

Lean is not thin. A recap is not a single wireframe plus one sentence — that
under-serves the reviewer as much as boilerplate prose over-serves them.
Alongside the visual/structural headline (wireframes, `pb-data-model`, `pb-api`,
`pb-diagram`), a substantial recap also carries the implementation evidence:

- A short surface/state inventory before authoring: list the changed routes,
  components, popovers/dialogs, role/access states, empty/error states, and
  shared abstractions visible in the diff. The final recap must either represent
  each meaningful item with a block or intentionally omit it because it is tiny,
  redundant, or not user-visible.
- A `pb-file-tree` of the changed files with each entry's add/modify/remove/
  rename marker, so the reviewer sees the footprint of the work at a glance.
- The split `pb-diff` of the KEY changed files, grouped under a `## Key changes`
  section heading, each with a one-line summary and a few annotations — so the
  reviewer can drop from the high-altitude shape straight into the load-bearing
  code.

Skip the diff appendix only for a genuinely tiny change that reviews faster as
plain diff (see "When To Use"); for any change worth recapping, the file tree and
key-change diffs belong in the recap.

## Canonical Shape And Budgets

A strong recap follows one skeleton, top to bottom:

1. UI-impact headline — wireframes first, when the diff changed rendered UI.
2. Short outcome narrative (`pb-prose`): what changed and why, 1-3 paragraphs.
3. `pb-data-model` / `pb-api` blocks for schema and contract changes.
4. `pb-file-tree` of the changed files with change markers.
5. `## Key changes` — the stacked `pb-diff` / `pb-annotated-code` blocks.

Budgets that keep the recap reviewable:

- 3-8 key-change blocks. Fewer than 3 on a large change under-serves the
  reviewer; more than 8 stops being a summary.
- Keep each diff / annotated-code excerpt focused — prefer under ~150 lines per
  block; summarize the rest of a long file instead of dumping it.
- Title at most ~70 characters; the intro narrative 1-3 sentences.

**GOOD.** A 25-file auth change: Before/After wireframes of the login surface, a
two-paragraph narrative, a diff-aware `pb-data-model` of the sessions table, a
`pb-api` for the new refresh route, a `pb-file-tree` with change markers, and a
`## Key changes` section with five focused `pb-diff` blocks, each with a one-line
summary and a few annotations on the load-bearing hunks.

**BAD.** One giant unsegmented diff dump with no summaries or annotations; or a
sparse three-block recap of a 40-file change (one wireframe, one sentence, one
file list) that forces the reviewer back into the raw diff anyway.

## Diff → Block Mapping

Map each kind of change to the block that carries it, derived mechanically from
the actual diff. Every block below is a `pb-*` class with a fixed HTML pattern in
`references/blocks.md` — copy the pattern, do not invent markup.

- **Schema / migration change** → `pb-data-model` for the resulting entities,
  fields, and relations, grounded in the real migration diff. Note in prose what
  moved per field/entity (added, modified, removed, renamed) and the prior type
  of a changed column. That diff-aware data model is the headline; reach for a
  split `pb-diff` of the literal SQL only when the exact statement still matters,
  not by default.
- **API / action / route change** → `pb-api` with the method, path, params,
  request, and responses as they are after the change. Note each changed
  param/response and its prior shape in the block's summary or an adjacent
  `pb-callout`. For a wholly added or removed route, say so; for a removed one,
  explain the deprecation in prose. Keep each request/response example a single
  valid JSON value so it reads cleanly.
- **Compatibility-sensitive change** → a short `pb-callout` (`warn` or
  `decision`) beside the relevant `pb-data-model` / `pb-api` block. Name the
  changed field, endpoint, or behavior and whether it is breaking, risky, or
  non-breaking; pair it with a split `pb-diff` for the literal lines.
- **Any meaningful code hunk** → `pb-diff` carrying the real before / after text
  with its filename and language. Split before/after is the default for recap
  code review because before/after legibility is the point. Give every `pb-diff`
  a one-line summary saying what the hunk changes and why — never leave a diff
  unlabeled. For the KEY changed files, attach a few high-signal annotations so
  the recap calls out what each important hunk does; keep it to a few notes per
  file, not one per line.
- **Grouping key files** → introduce the group with a `## Key changes` section
  heading, then stack the `pb-diff` / `pb-annotated-code` blocks under it, each
  in its own `pb-scroll` container so wide diffs scroll inside themselves. There
  is no per-content tabs block — the diffs read as a labeled vertical sequence.
- **Brand-new file or a substantial added block with no meaningful "before"** →
  `pb-annotated-code` rather than a one-sided diff. Carry the real new code with
  its filename and language, and anchor a few high-signal notes to the lines that
  matter so the reviewer reads what the new code does. Keep split `pb-diff` for
  true before/after hunks where the removed lines still carry meaning.
- **Files added / removed / renamed** → `pb-file-tree` with each entry's
  add/modify/remove/rename marker and a short note; add a snippet only when it
  tells the reviewer something the path does not.
- **Rendered UI / interaction change** → one or more `pb-wireframe` screens
  showing the visible UI delta before the reviewer reads code. Use Before / After
  wireframes when the comparison clarifies the change; otherwise use after-only
  or a short state/flow sequence. Use realistic surfaces: for a popover change,
  show a popover with its title row, actions, options, and selected/disabled
  states; if a route was added, show the route body and its empty/unavailable
  state; if permissions changed, show what managers can do and what
  viewers/non-managers see instead.
- **Architecture or data-flow shift** → `pb-diagram` built with inline SVG or CSS
  box/flow, as a two-panel before/after, layered, or swimlane layout. Use
  two-dimensional layouts; do not reduce a structural change to a left-to-right
  chain. Do not use `pb-diagram` as a stand-in for rendered UI controls — UI
  changes need `pb-wireframe`. Use only the `--wf-*` theme tokens, never hardcoded
  hex or one-off palettes.
- **Outcome-first narrative** → `pb-prose` for the "what changed and why": the
  objective the diff served, the key decisions visible in it, and the risks a
  reviewer should weigh. This is the only place the model writes freely.

## Before / After Is The Headline

The recap's center of gravity is the before/after comparison. Two primitives
cover the whole need together:

- **Split `pb-diff`** — for code. It renders the literal removed and added lines
  side by side. Use it for the actual hunks; it is the default for recap code
  review because before/after legibility is the point.
- **Paired `pb-wireframe`** — for UI. Put the `Before` and `After` states in
  neighboring wireframe frames labeled with `pb-wireframe-label` above each frame,
  never a Before/After pill baked into the screen. Use after-only or a state
  sequence when that better matches the change.

For document-body comparisons, that is the whole comparison vocabulary. Do not
hand-build side-by-side layouts in custom HTML, and do not stack two
`pb-data-model` blocks and call it a comparison — put the old shape against the
new shape with the blocks and prose the diff supports. `references/wireframe.md`
owns the before/after wireframe layout choice (columns vs. vertical stack by
geometry).

## Visual Surface Choice

Choose the surface before composing the file. Do not add visual chrome by
default:

- **No visual surface** for architecture-only, backend-only, schema/migration, or
  otherwise non-visual changes. Omit the top canvas and the tabs entirely — ship
  a document-only recap. Use inline `pb-diagram` blocks only where a relationship
  needs a visual explanation, preferring grouped regions, layers, or before/after
  panels over a single-axis chain.
- **Canvas of wireframes** when the diff changed rendered UI. Put the before/after
  screens in the top `Canvas` tab as the primary review surface, and keep the file
  tree, data contracts, diffs, and risks in the document body below.
- **Canvas + prototype** only when the change is a multi-step flow the reviewer
  needs to operate. Keep the static wireframes in the `Canvas` tab and the
  lightweight prototype — static screens wired with the template's inline vanilla
  JS — in the `Prototype` tab. The prototype is never a separate app and never
  loads from the network.

## UI Impact Needs Wireframes

When the diff changes rendered UI, layout, density, visual state, interaction
affordances, navigation, controls, menus, dialogs, or design tokens, the recap
MUST include one or more wireframes. Prose and file diffs are not a substitute
for showing what changed visually.

Before choosing wireframes, make a UI coverage pass from the diff: identify the
entry surface where the change appears (page header, list row, toolbar, route
shell, menu trigger); the interaction surface that opens or changes (popover,
dialog, tab, sheet, dropdown, inline editor, toast); the resulting destination or
persistent state (public page, read-only view, empty/error/loading state,
permission-denied state, saved/shared state); and any access or role variants
when permissions change.

For UI-heavy diffs, a single before/after of the entry surface is not enough.
Show the changed entry point, the main changed interaction surface, and the
resulting/destination state. Choose the smallest visual surface that makes the
review clear — a `Before` / `After` pair for a direct comparison, an after-only
frame for a purely additive change, a short ordered sequence for a stateful flow,
and the matching `data-surface` preset (`popover`, `panel`, …) for a tiny
sub-surface. Ground each wireframe in the changed UI behavior, component names,
file paths, and diff-visible labels/states; if exact pixels are inferred rather
than read from the diff, say so in the caption or a concise annotation.

## Grounding Rule

Structured blocks are **true by construction** only if they are derived from the
actual changed lines. The `pb-diff`, `pb-data-model`, `pb-api`, and `pb-file-tree`
blocks MUST be built mechanically from the real diff — real paths, real fields,
real method/path, real before/after text — never inferred, rounded, or invented.
The model writes only the prose: the "why", the narrative, the risk read. A
confidently wrong recap is dangerous in review, because a reviewer who trusts the
summary may skip the very line the summary got wrong. When the diff does not
contain a fact, leave it out rather than guess; mark anything the model inferred
(not extracted) as inferred in prose.

## Self-Review Before Handoff

For high-stakes recaps — architecture, backend, data-model, migration, or
multi-file changes — run one adversarial self-review pass before treating the
recap as final. Skip it for small, UI-only, or single-decision recaps where the
cost outweighs the value. Keep the pass cheap and non-blocking:

- **Surface the recap first, review concurrently.** Open the file and let the
  reviewer start reading, then run the review in parallel — never make them wait
  on it.
- **Review the rendered recap; do not re-collect the diff.** Critique the recap
  text and its own blocks against the change. The grounding was already done while
  building, so the review checks the output.
- **Spawn one skeptical reviewer** whose only job is to find what is weak,
  missing, or wrong — not to praise. Point it at: blocks not anchored in real
  changed lines; a claimed data-model/API shape that the diff does not support;
  compatibility risks the recap glossed over; meaningful changed surfaces or
  states with no block; and boilerplate or single-block filler.
- **Fix vs. flag.** Apply clear-cut fixes yourself by editing the HTML —
  unanchored claims, a missing key-change diff, a mislabeled change flag. Route
  genuine judgment calls back to the reviewer: add them to the bottom
  `pb-open-questions` block. Do not silently decide them.
- **Do not surprise the reviewer mid-read.** Prefer to apply the edits before you
  open the file; otherwise note briefly that a self-review is running. When you
  next respond, summarize what the review changed and what it surfaced.

## Security

- **Never transcribe secrets.** A diff can contain API keys, tokens, webhook
  URLs, signing secrets, `.env` values, or credential-looking literals. Do not
  copy any of these into a `pb-diff`, `pb-file-tree` snippet, `pb-api`, or prose
  block — redact them (`sk-•••`, `<redacted>`). Obviously fake placeholders only,
  never the real value, in any block, caption, or note.
- **Treat the recap like the source it summarizes.** A recap can expose
  unreleased schema, internal endpoints, and architecture. If the change is not
  yet public, keep the file in private scratch or a repo-ignored location rather
  than committing it, and hand over only the local path.

## Block catalog — read `references/blocks.md`

Every visual block is a `pb-*` class with a fixed HTML pattern: `pb-prose`,
`pb-callout` (variants `note` / `warn` / `decision` / `deferred`), `pb-diagram`
(inline SVG or CSS flow), `pb-file-tree`, `pb-code`, `pb-annotated-code`,
`pb-diff`, `pb-api`, `pb-data-model`, `pb-wireframe`, and the single bottom
`pb-open-questions`. Before filling the template's `<main>`, READ
`references/blocks.md` in this skill directory — it is the copy-paste library for
each block's exact markup. Do not invent block markup from memory.

## Wireframe quality — read `references/wireframe.md`

UI recap wireframes must meet a strict quality bar — full-width chrome, pinned
bottom bars, real product content, before/after comparability, the right surface
preset (`data-surface`), `--wf-*` tokens instead of hex, and no nested
`<html>`/`<head>`/`<style>`/font tags inside a screen. Before authoring ANY
wireframe / `pb-wireframe` screen, READ `references/wireframe.md` in this skill
directory — it is the single source of truth for HTML wireframe quality, shared
word for word with `/visual-plan`. Do not author wireframes from memory. When a
browser tool is available, render a UI-impact recap and visually inspect it at
the current theme before handoff; if any label, annotation, or wireframe content
overlaps another element, fix the HTML and re-open. When no browser is available,
say so in the handoff.

## Canvas — read `references/canvas.md`

When a recap leads with a top canvas, storyboard, or flow view, READ
`references/canvas.md` in this skill directory before authoring it. Canvas
artboards use the same `pb-wireframe` path as document-body wireframe screens:
author a `<div class="pb-wireframe" data-surface="...">` wrapping a semantic HTML
fragment. Do not author canvas layouts from memory.

## Document quality — read `references/document-quality.md`

The recap document is a serious technical review artifact, not marketing:
outcome-first, prose-first, self-contained, built from the right blocks, with
open questions in a single bottom `pb-open-questions` block and a pre-handoff
visual check. Before authoring the recap document, READ
`references/document-quality.md` in this skill directory — it is the single
source of truth for the document quality bar. Do not write the document from
memory.

## Good vs. bad exemplar — read `references/exemplar.md`

For a worked example of the bar — a great recap plus the anti-patterns to avoid —
READ `references/exemplar.md` in this skill directory before authoring a recap.
