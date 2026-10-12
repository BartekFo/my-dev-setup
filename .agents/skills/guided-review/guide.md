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
      {"id": "main", "label": "Main screen", "sub": "MainActivity", "kind": "PAGE", "status": "unchanged"},
      {"id": "take", "label": "Share intake", "sub": "ShareViewModel.takeShare()", "kind": "SVC",
       "status": "added", "chapter": 2, "focal": true}
    ],
    "edges": [{"from": "main", "to": "take", "label": "optional", "kind": "call"}]
  },
  "sequence": {
    "title": "A shared file is uploaded",
    "actors": [
      {"id": "take", "label": "Share intake", "sub": "ShareViewModel", "kind": "SVC"},
      {"id": "api", "label": "Upload API", "sub": "POST /files", "kind": "API"}
    ],
    "messages": [
      {"from": "take", "to": "api", "label": "upload(file)", "kind": "http", "status": "added",
       "chapter": 2, "note": "Optional short note."}
    ]
  },
  "tree": [
    {"label": "ShareScreen", "path": "src/share/ShareScreen.tsx", "status": "added", "chapter": 2,
     "inputs": ["threadId"], "outputs": ["sent"],
     "detail": "Optional, one line: state it owns, when it mounts.", "children": []}
  ],
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
  status "removed", so the diagram shows before and after at once. At most 9
  nodes and 12 edges. Merge nodes that always travel together (a route and its
  guard; a cell and its draft state). Above budget, cut the least important
  neighbours. Every non-unchanged node names the chapter that holds its change.
- flow node text: "label" is the human name; "sub" is the code identifier
  (class, path or endpoint). Never pack both into "label". "kind" is an
  uppercase tag of at most 6 characters (PAGE, SVC, API, QUEUE, DLG, CELL,
  ROUTE, STORE). "focal": true marks the 1-2 nodes at the core of the change,
  especially when every node has the same status.
- flow edge "kind": "call" (default), "http" for network calls, "writeback"
  for a result flowing back to its owner, "rewired" for a kept edge whose
  endpoints changed. Edge labels are at most 24 characters.
- sequence: optional. Add it only when the PR adds or changes an ordered
  interaction between 2-5 participants (request/response, save queue, retries,
  event handshake, auth redirect) where order matters and the flow graph cannot
  show it. Omit it otherwise. At most 5 actors and 12 messages, in time order.
  Actors use the same "label", "sub" and "kind" as flow nodes. Message "kind":
  "call" (default), "return", "async" or "http". Labels are at most 32
  characters; "note" is at most 60. Mark added and removed messages with
  "status", so the diagram shows before and after. Every non-unchanged message
  names its chapter.
- tree: optional. Add it when the PR adds or reshapes a component, module or
  class hierarchy. Nest by real ownership (parent renders or creates child).
  status defaults to "unchanged"; every other status names its chapter.
  path is the full repo path from the diff, so the name links to its diff.
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
