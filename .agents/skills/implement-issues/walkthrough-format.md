# Walkthrough format

Format for the end-of-batch walkthrough (step 5 of `implement-issues`). Plain-English prose over exhaustive line-by-line; small faithful code sketches over verbatim dumps.

- `#` title — one plain-English line naming what the batch delivered.
- `📋 TLDR` — 2-3 short sentences giving the gist to someone who didn't write it. Optional single `mermaid` block only if a flow/handoff is easier to grasp visually. Then a `---` rule.
- One or more `##` sections, each:
  1. plain-English title with at least one emoji,
  2. a one- or two-sentence lead-in,
  3. exactly one fenced code block (~10 non-blank lines or fewer; use `...`/placeholders/simplified identifiers; short intent comments on key lines explaining what + why).
  - Stop the section after its code block. Separate body sections with `---`.

Guardrails: no prose-only `##` sections, no text after a section's code block, no secrets/long literals (use placeholders), don't invent intent the code doesn't support.
