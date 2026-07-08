---
name: implement-issues
description: Serially implement a batch of pre-written issues, each via a subagent, with a human review gate before every commit.
disable-model-invocation: true
---

# Implement Issues

Serial, human-gated execution of a batch of issues. The main thread **orchestrates only** — never writes code itself; each issue's implementation and its review fixes run in a Sonnet subagent. Per issue, one at a time (never parallel): dispatch → code review + auto-fix → human gate → commit. On approve, optionally work through the slice with `teach-me-changes` first. After the batch, write a scannable walkthrough.

## Inputs

User invokes: `/implement-issues <path>`

`<path>` resolves to one of:
- Directory containing `*.md` issue files
- Single markdown file listing multiple issues
- File with newline-separated issue tracker refs (URLs or IDs) — fetch each via the issue tracker

If `<path>` missing or unreadable, ask user for it. Otherwise no further questions — proceed.

## Workflow

### 1. Load issues

Read every issue. For each capture: `id` (filename or tracker id), `title`, `body`, `acceptance criteria`, `blocked by`.

### 2. Sort by dependency

Topological sort using `Blocked by`. Detect cycles → stop, report to user.

Show user the planned order as numbered list (title + id only). Wait for user "go" / approval of order. User may reorder or skip.

### 3. Loop per issue

Before starting, record the run's baseline commit: `git rev-parse HEAD` → `BASE_SHA`. Step 5 uses it to scope the final walkthrough.

For each issue in approved order:

#### 3a. Dispatch subagent

Use `Agent` tool. Required params:
- `subagent_type: "issue-implementer"` (standing rules — TDD mode selection, no-commit, lint/typecheck/test, reporting format — live in the agent definition)
- `model: "sonnet"` (latest Sonnet; the agent also defaults to it)
- `description`: short 3-5 word task name
- `prompt`: self-contained issue brief (see template below)

The main thread orchestrates — never implement in it. Always delegate to the subagent.

<subagent-prompt-template>
Implement this issue. Follow your standing rules: pick testing mode (TDD / Safety-net / No-test), no commit, run lint/typecheck/tests, report back in the standard format.

Issue id: {id}
Title: {title}

Full issue body:
---
{body}
---

Acceptance criteria:
{acceptance_criteria_checklist}

{optional — only when re-dispatching after reject}
Reviewer feedback from previous attempt (treat as highest-priority constraints):
---
{feedback}
---
</subagent-prompt-template>

#### 3b. Code review + auto-fix

After subagent returns, before surfacing to the user:

1. Invoke the `requesting-code-review` skill (`Skill` tool, `skill: "superpowers:requesting-code-review"`) on the just-implemented changes.
   - The subagent did NOT commit, so the changes live uncommitted in the working tree. `requesting-code-review` defaults to committed SHAs (`BASE_SHA=HEAD~1`, `HEAD_SHA=HEAD`), which would miss them. Set `BASE_SHA` to the current `HEAD` and direct the reviewer subagent at the working-tree diff: `git diff HEAD` plus any untracked files. Pass that scope when dispatching the reviewer.
2. Collect the reviewer's findings (Critical / Important / Minor).
   - **No findings** → skip straight to 3c.
   - **Findings exist** → re-dispatch the `issue-implementer` subagent (same params as 3a) with the findings placed in the feedback slot of the prompt template. Instruct it to apply the fixes (prioritise Critical + Important), no commit, re-run lint/typecheck/tests.
3. One review + one fix pass is enough. Do not loop the review — the human gate in 3c catches anything left. (`reject` in 3d returns here, so re-reviews happen on demand.)
4. Main agent never writes the fixes itself — always delegate to the subagent.

#### 3c. Surface diff to user

After review + fixes:
- Run `git status` + `git diff` to confirm actual changes (subagent summary ≠ truth — verify).
- Print compact summary: issue id, files changed, subagent test/lint results, and what the code review flagged + fixed.
- Explicitly state: "Awaiting code review. Reply `approve` to commit + continue, `reject` with feedback to revise, or `skip` to move on without commit."

STOP HERE. Do not continue to next issue. Do not auto-commit. Wait for user reply.

#### 3d. On user response

- **approve** → teach gate (3e) → commit (3f) → next issue.
- **reject** → re-dispatch subagent with the user's feedback appended to the prompt, then return to step 3b (re-review + re-fix, then surface again).
- **skip** → leave changes as-is (or ask user if they want them reverted). Move to next issue.
- **abort** → stop whole loop.

#### 3e. Teach gate (opt-in)

After `approve`, before committing, offer to work through what was just built — while the slice is small and fresh.

- If the batch `skip-all` flag is set, skip this step entirely.
- Otherwise ask: "Work through this slice? `yes` / `no` / `skip-all`."
  - **yes** → invoke the `teach-me-changes` skill (`Skill` tool, `skill: "teach-me-changes"`), scope = this issue (its diff, body, relevant PRD slice). When it returns, proceed to commit.
  - **no** → proceed to commit.
  - **skip-all** → set the batch flag (no more teach prompts this run), proceed to commit.

The teaching session does not commit anything itself — control returns here for the commit.

#### 3f. Commit

Use issue title + id as commit subject. Example:
```
feat: {title} ({id})
```
Match repo's existing commit style — check `git log` first. Stage only files the subagent touched.

Never use `--no-verify`. If pre-commit hook fails, surface the error to user, do NOT amend, do NOT bypass.

### 4. Done

After last issue: report summary — committed N, skipped M, aborted at K. Mention any uncommitted changes left in working tree.

### 5. Explain the batch

After the summary, write one scannable walkthrough of everything implemented this run. Scope = the cumulative diff `BASE_SHA..HEAD` (skip if nothing was committed). Follow the format in [`walkthrough-format.md`](walkthrough-format.md).
