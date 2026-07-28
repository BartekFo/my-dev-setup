---
name: commit
description: Commit working tree changes with a conventional commit title (max 100 chars) and a body describing the changes.
disable-model-invocation: true
---

# Commit

Commit the current working tree changes with a well-formed message.

## Steps

1. Inspect the changes: run `git status` and `git diff HEAD`. Read every changed file's diff before writing the message. If the working tree is clean, report that and stop.
2. Stage everything relevant: `git add` all working-tree changes, unless the user scoped the commit to specific files.
3. Compose the message:
   - **Title**: Conventional Commits format `type(scope): summary`, max 100 characters. Derive the type from the diff (feat, fix, refactor, chore, test, docs, ci, build, perf). When the branch name contains a ticket id (e.g. `CON-1234`), use it as the scope.
   - **Body**: always present, never empty. 1–4 sentences describing what changed and why, covering every staged file's purpose in the change.
4. Commit and verify: create the commit, then run `git log -1 --stat` and confirm the title length is ≤ 100 characters and every intended file is included. Show the result to the user.
