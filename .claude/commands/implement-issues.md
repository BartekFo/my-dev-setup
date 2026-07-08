---
description: Implement a batch of issues one-by-one via Sonnet subagents with per-issue human code review gates.
argument-hint: <path-to-issues-file-or-dir>
---

Invoke the `implement-issues` skill via the Skill tool. Pass the user-supplied path as the input.

Path argument: $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user for the path to the issues file or directory before starting. Otherwise hand the path to the skill and follow the skill workflow exactly — dependency-sort, dispatch one Sonnet subagent per issue, pause for review after each, commit on approve, then continue.
