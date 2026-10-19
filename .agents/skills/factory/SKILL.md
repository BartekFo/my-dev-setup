---
name: factory
description: Turn a user story and an implementation plan into a GitHub stacked PR (gh stack), one reviewed layer per ticket. Runs autonomously; the human only reviews before merge.
disable-model-invocation: true
model: opus
argument-hint: "<story: path | issue ref> <plan: path | issue ref>"
---

# Factory

Autonomous shipping of one story as a **GitHub stacked PR**, one layer per ticket, managed with the `gh stack` extension. The human gate is the PR review before merge, not the session. The main thread **orchestrates only**: it never writes code and never reads full diffs. The ledger is the only state; after any compaction, re-read it before the next action.

## Models

Dispatch every subagent with an explicit model. An omitted model inherits the session's — usually the most capable and most expensive available.

| Model    | Runs                                                                              |
| -------- | --------------------------------------------------------------------------------- |
| `opus`   | the main thread (orchestration); the Spec and Standards review axes               |
| `sonnet` | everything else: ticket import and drafting, every implementer, every fixer, the Simplify and Tests axes |

Never dispatch an implementer or a fixer on `opus`, whatever the ticket size.

## Context rules

- Briefs carry paths, never pasted file contents or diffs.
- Every subagent ends with the report below and nothing else. No diffs, no logs, no narration.
- Reviewers never see the implementer's report. They get the ticket and the diff command only.
- The main thread inspects changes with `git diff --stat` only.

```
status: done | blocked | findings
files: <touched paths>
checks: <command → pass/fail>
findings: <max 10, each `path:line — problem → fix`, tagged hard | judgement>
notes: <max 3 lines a later ticket needs>
```

## Run directory

```
${TMPDIR:-/tmp}/factory/<repo-name>/<story-slug>/
  ledger.md        # one row per ticket
  tickets/NN-<slug>.md
  standards.md     # review inputs, built once
  wt/NN/           # worktree of a parallel wave row
```

`<repo-name>` is the basename of `git rev-parse --show-toplevel`. Nothing in this directory is committed.

## Workflow

### 1. Intake

Read the story and the plan in full. Read the root and scoped `CLAUDE.md` / `AGENTS.md`.

If the story or an imported ticket has no testable acceptance criteria, stop and ask. This is the only question before the PRs. For any other gap, pick the option the plan and codebase support best and record it as an assumption.

The working tree must be clean. Run `git worktree prune` to drop worktrees the OS removed from `$TMPDIR`. Fetch, and set `trunk` = the remote default branch (`git symbolic-ref refs/remotes/origin/HEAD`).

`gh extension list` must show `github/gh-stack`. Otherwise stop and tell the user to run `gh extension install github/gh-stack`.

### 2. Tickets

Look for tickets the story already has: tracker sub-issues or linked issues, or ticket files the story or plan points to. Skip tickets the tracker marks done.

**Import (subagent, `sonnet`)** when tickets exist. It writes one file per ticket with the local ticket template of mattpocock `to-tickets`, and keeps each ticket's title, acceptance criteria, blocking edges, and tracker reference. It never splits, merges, or redrafts a ticket. Missing blocking edges come from the plan, recorded as assumptions.

**Draft (subagent, `sonnet`)** when no tickets exist, or for only the story acceptance criteria that no imported ticket owns. Brief: story path, plan path, run directory, the imported ticket files, and the "Draft vertical slices" rules of mattpocock `to-tickets` (newest `~/.claude/plugins/cache/*/mattpocock-skills/*/skills/engineering/to-tickets/SKILL.md`, step 3). The plan decides the order and the seams; the slicing rules decide the size.

It writes one file per ticket with that skill's local ticket template, plus an **Assumptions** list, and returns the report. Skip that skill's quiz step.

Order the tickets in one linear sequence that respects every blocking edge, keeping plan order on ties. This order is the stack order. Write the ledger:

```
| NN | title | blocked-by | status | branch | base | sha | pr | notes |
```

`status` is one of `todo`, `in-progress`, `done`, `draft`. `base` is the commit the layer starts from.

### 3. Review inputs (once)

Follow step 3 of mattpocock `code-review`: find the repo's standards sources. Write their paths and the smell baseline into `standards.md`. Every Standards reviewer reads this file instead of searching again.

### 4. Loop per wave

A wave is every `todo` row whose `blocked-by` rows are all `done`, in ledger order, max 3 rows. A wave of one row runs 4a–4f in the main checkout. A larger wave runs per **Parallel wave**.

#### 4a. Layer

Name the branch per the repo's branch convention, else `factory/<story-slug>/<NN>-<slug>`.

- First row: `gh stack init --base <trunk> <branch>`.
- Later rows: from the top branch of the stack, `gh stack add <branch>`.

Record `base` = `git rev-parse HEAD`. Set the row to `in-progress`.

#### 4b. Implement (subagent)

Brief: the ticket path, the `notes` of done rows, and the rules below. Model: `sonnet`.

- Implement exactly the ticket's acceptance criteria. Nothing else.
- Use /tdd where possible, at pre-agreed seams. Avoid tdd for frontend components.
- Run typechecking and single test files regularly, and the full test suite once at the end.
- Commit per 4d after each green step. Leave the tree clean on return.

#### 4c. Review + auto-fix

Spawn four axes in one message, each a fresh subagent with its model per **Models**, all on `git diff <base>..HEAD`. Each reports only and edits nothing.

- **Standards**: brief per mattpocock `code-review` step 4, with standards from `standards.md`.
- **Spec**: brief per mattpocock `code-review` step 4, with the ticket as the spec.
- **Simplify**: read `~/.claude/skills/simplify/SKILL.md` and apply it.
- **Tests**: read `~/.claude/skills/test-gate/SKILL.md`. For each test the diff adds or changes, answer the four gate questions and name every tautology form it matches. Also list acceptance criteria with no owner test.

Collect findings without reranking across axes.

- **No hard findings** → 4d.
- **Hard findings** → dispatch one fixer (`sonnet`) with the ticket path and the hard findings verbatim. It commits per 4d. Then rerun only the axes that had hard findings, once. Do not loop further.

#### 4d. Commit rules

The implementer and the fixer commit their own work. Brief both with these rules:

- Read and follow `~/.claude/skills/commit/SKILL.md`.
- One commit per atomic, green step. Each commit passes the hooks on its own.
- Never use `--no-verify`, never amend, never bypass. If a hook fails, fix the cause and commit again.

After the fix round, `git status --porcelain` must print nothing. Otherwise dispatch one fixer to commit the rest.

#### 4e. Pull request

Run `gh stack submit --auto`. It pushes every branch, opens this layer's PR as a draft on the correct base, and links it into the stack on GitHub.

Then set the title and body with `gh pr edit <branch> --title <title> --body-file <file>`. Title: a conventional commit summary of the ticket. Body: the repo's `.github/pull_request_template.md` if it exists, else the mattpocock `pr` template. Add a **Ticket** section (the acceptance criteria), the ticket's **Assumptions**, and the remaining review findings per axis.

Record `sha` and `pr` in the row, and write `notes` that later tickets need.

#### 4f. Stop rule

A ticket is `draft` when hard findings or failing checks remain after the fix round, or the implementer returns `blocked`. Commit what remains per 4d, keep its PR as a draft, and put the cause first in the body. Every later layer stacks on it, so stop the loop after the current wave lands.

Otherwise run `gh pr ready <branch>` and set the row to `done`.

A `gh stack` exit code other than 0 stops the run. Report the code: 9 means stacked PRs are not enabled for this repository, 8 means another process locks the stack.

#### Parallel wave

The rows of a wave do not depend on each other, so they build in parallel and land one by one.

1. For each row, run `git worktree add --detach <run>/wt/NN <top>`, where `<top>` is the top branch of the stack, else `trunk`. Run the repo's fresh-checkout setup from `AGENTS.md` / `CLAUDE.md` in it. If that setup does not create the env files, copy them from the main checkout: the patterns in `.worktreeinclude` if it exists, else every gitignored `.env*` file except `*.example`, at the same relative paths. Copy, never symlink. Set the row to `in-progress`.
2. Dispatch every implementer (4b) in one message. Each brief adds the worktree path and this rule: start every Bash command with `cd <worktree> && ` and give file tools absolute paths under it.
3. Run 4c per row as soon as its implementer returns, with the diff command `git -C <worktree> diff <base>..HEAD`, where `<base>` is the sha of `<top>` at step 1.
4. When all rows finish 4c, record each row's `head` = `git -C <worktree> rev-parse HEAD`.
5. Land the rows in ledger order, `done` candidates before `draft` candidates. For each row, run `git merge-tree --write-tree --merge-base <base> <current top> <head>`. A non-zero exit means the row overlaps an earlier row: set it back to `todo` for the next wave. Otherwise run 4a, `git cherry-pick <base>..<head>`, then 4e–4f.
6. Remove each worktree with `git worktree remove --force <run>/wt/NN`.
7. The landed layers never ran checks together. Run the full test suite once on the top branch. If it fails, set the top row to `draft`, run `gh pr ready --undo <branch>`, put the failure first in its PR body, and stop the loop.

### 5. Report

From the ledger: PR URLs bottom to top with their status, every draft cause, every assumption, and the tickets not started. Add `gh stack view --short`.

Tell the user to merge bottom-up, or to merge the top PR to land the whole stack. GitHub rebases the remaining layers after each merge.

Then remove every worktree left under `<run>/wt/` with `git worktree remove --force`, and delete the run directory. This also runs when the loop stops early.
