# Guide Prompt Template

Dispatch one foreground `general-purpose` subagent. Fill the `{PLACEHOLDERS}`.

```
You are writing a reading guide for pull request #{NUMBER} in {OWNER_REPO}.
A guide tells a human reviewer what the PR does and in which order to read it.
It explains; it does not judge. Defects, risks and suggestions are out of scope.

## Inputs

- PR metadata: {DIR}/pr.json
- Diff: {DIR}/diff.patch
- Hunk index: `python3 {SKILL_DIR}/render.py hunks {DIR}`

Read source files in the working tree wherever the diff alone cannot explain a
change. Leave the repository untouched; the only file you write is
{DIR}/guide.json.

## guide.json

{
  "overview": "One sentence: the problem the PR solves and how.",
  "steps": ["What the PR does, in causal order, 2-6 items."],
  "flow": {
    "title": "What the diagram traces, e.g. 'Shared content reaches a thread'",
    "nodes": [
      {"id": "main", "label": "MainActivity", "status": "unchanged"},
      {"id": "take", "label": "takeShare()", "status": "added", "chapter": 2}
    ],
    "edges": [{"from": "main", "to": "take", "label": "optional"}]
  },
  "chapters": [
    {
      "title": "Stage and upload shared files",
      "summary": "What this chapter changes and why. 1-2 short paragraphs, plain words, `code` in backticks.",
      "note": "Optional: the one non-obvious rule the reader must hold to judge this chapter.",
      "collapsed": false,
      "files": [
        {"path": "src/share/send.ts"},
        {"path": "src/auth.ts", "hunks": [1, 3]}
      ]
    }
  ]
}

## Rules

- flow: the runtime path the PR changes: calls, events, data moving between
  components. One node per function, component, endpoint or table. Keep the
  unchanged neighbours a reader needs for orientation. Removed nodes stay with
  status "removed", so the diagram shows before and after at once. At most 12
  nodes. Every non-unchanged node names the chapter that holds its change.
- chapters: one idea each, in reading order: the core behaviour change first,
  then its callers and integration points, then configuration and
  infrastructure, then database and migrations, then tests, then generated
  files and lockfiles with "collapsed": true.
- note: an invariant, an ordering constraint or a trade-off the code relies
  on. Omit the field when there is none.
- files: every file in the diff lands in exactly one chapter. Split a file
  only when its hunks serve different ideas; list "hunks" with indices from the
  hunk index, and every hunk lands in exactly one chapter.
- A diff with fewer than 5 files gets one chapter.

## Done when

`python3 {SKILL_DIR}/render.py check {DIR}` exits 0. It prints every coverage
and schema error; fix them all and rerun.

Your final message is data for the dispatching agent: the word "ok" and the
chapter titles, one per line.
```
