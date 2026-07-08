---
description: Ship a batch of tickets one-by-one — implement + code-review in Sonnet subagents, per-ticket human gates.
argument-hint: <path-to-tickets-file-or-dir>
---

Invoke the `ship-tickets` skill via the Skill tool. Pass the user-supplied path as the input.

Path argument: $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user for the path to the tickets file or directory before starting. Otherwise hand the path to the skill and follow the skill workflow exactly — dependency-sort, implement each ticket in a Sonnet subagent, code-review it, pause for the human gate, commit on approve, then continue.
