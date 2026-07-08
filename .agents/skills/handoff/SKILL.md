---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Create the file with the command below, then write to that `.md` path (read the file before you write to it):

```bash
f="$(mktemp "${TMPDIR:-/tmp}/handoff-XXXXXX")" && mv "$f" "$f.md" && printf '%s\n' "$f.md"
```

(Pass a full path template ending in trailing `X`s and avoid `-t`; both GNU and BSD/macOS `mktemp` substitute trailing `X`s the same way. BSD only substitutes trailing `X`s, so the `.md` suffix is added via `mv` rather than in the template.)

Suggest the skills to be used, if any, by the next session.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
