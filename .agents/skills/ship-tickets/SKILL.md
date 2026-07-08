---
name: ship-tickets
description: Ship a batch of pre-written tickets serially — implementation via the `implement` skill and review via `code-review`, both executed by Sonnet subagents, with a human gate before every commit.
disable-model-invocation: true
---

# Ship Tickets

Serial, human-gated shipping of a ticket batch. The main thread **orchestrates only** — never writes code itself. Per ticket, one at a time (never parallel): implement (Sonnet subagent driving the `implement` skill) → code review (`code-review` skill, its axis sub-agents on Sonnet) + auto-fix → human gate → commit. On approve, optionally work through the slice with `teach-me-changes` first. After the batch, a Sonnet subagent writes the walkthrough via the `explain-code` skill.

## Inputs

User invokes: `/ship-tickets <path>`

`<path>` resolves to one of:
- Directory containing `*.md` ticket files
- Single markdown file listing multiple tickets
- File with newline-separated issue tracker refs (URLs or IDs) — fetch each via the issue tracker

If `<path>` missing or unreadable, ask user for it. Otherwise no further questions — proceed.

## Workflow

### 1. Load tickets

Read every ticket. For each capture: `id` (filename or tracker id), `title`, `body`, `acceptance criteria`, `blocked by`.

### 2. Sort by dependency

Topological sort using `Blocked by`. Detect cycles → stop, report to user.

Show user the planned order as numbered list (title + id only). Wait for user "go" / approval of order. User may reorder or skip.

### 3. Loop per ticket

Before starting, record the run's baseline commit: `git rev-parse HEAD` → `BASE_SHA`. Step 5 uses it to scope the final walkthrough.

For each ticket in approved order:

#### 3a. Implement (subagent)

Use `Agent` tool. Required params:
- `subagent_type: "ticket-implementer"` — a thin wrapper over the `implement` skill; the standing overrides (no commit, no self-review, seams from acceptance criteria) and the reporting format live in the agent definition
- `model: "sonnet"` (always the latest Sonnet — never inherit the session model)
- `description`: short 3-5 word task name
- `prompt`: self-contained ticket brief (see template below)

Even a one-line ticket goes through the subagent — orchestrate only.

<subagent-prompt-template>
Implement this ticket. Follow your standing rules: drive the work through the `implement` skill, no commit, no self-review, run lint/typecheck/tests, report back in the standard format.

Ticket id: {id}
Title: {title}

Full ticket body:
---
{body}
---

Acceptance criteria:
{acceptance_criteria_checklist}

{optional — only when re-dispatching after review findings or reject}
Reviewer feedback from previous attempt (treat as highest-priority constraints):
---
{feedback}
---
</subagent-prompt-template>

#### 3b. Code review + auto-fix

After the subagent returns, before surfacing to the user, review via the `code-review` skill (`Skill` tool, `skill: "code-review"`). It runs its two axes — Standards and Spec — as parallel sub-agents; dispatch both with `model: "sonnet"`. Three adaptations for this loop:

- **Fixed point = `HEAD`.** The implement subagent did not commit, so the diff under review is the working tree: point both axis sub-agents at `git diff HEAD` plus untracked files — not `<fixed-point>...HEAD`. The non-empty check runs against that working-tree diff.
- **Spec source = the ticket.** Pass `{body}` + acceptance criteria straight to the Spec sub-agent — skip the skill's commit-message / issue-tracker hunt.
- **Model.** Both axis sub-agents get `model: "sonnet"`.

Then:

1. Collect findings from both axes.
   - **No findings** → skip straight to 3c.
   - **Findings exist** → re-dispatch the `ticket-implementer` subagent (same params as 3a) with both axes' findings in the feedback slot of the prompt template. Instruct it to apply the fixes (Spec gaps and hard Standards violations first; baseline smells are judgement calls), no commit, re-run lint/typecheck/tests.
2. One review + one fix pass is enough. Do not loop the review — the human gate in 3c catches anything left. (`reject` in 3d returns here, so re-reviews happen on demand.)
3. Fixes are orchestrate-only too — the subagent applies them.

#### 3c. Surface diff to user

After review + fixes:
- Run `git status` + `git diff` to confirm actual changes (subagent summary ≠ truth — verify).
- Print compact summary: ticket id, files changed, subagent test/lint results, and what each review axis (Standards / Spec) flagged + what was fixed.
- Explicitly state: "Awaiting code review. Reply `approve` to commit + continue, `reject` with feedback to revise, or `skip` to move on without commit."

STOP HERE. Do not continue to next ticket. Do not auto-commit. Wait for user reply.

#### 3d. On user response

- **approve** → teach gate (3e) → commit (3f) → next ticket.
- **reject** → re-dispatch subagent with the user's feedback appended to the prompt, then return to step 3b (re-review + re-fix, then surface again).
- **skip** → leave changes as-is (or ask user if they want them reverted). Move to next ticket.
- **abort** → stop whole loop.

#### 3e. Teach gate (opt-in)

After `approve`, before committing, offer to work through what was just built — while the slice is small and fresh.

- If the batch `skip-all` flag is set, skip this step entirely.
- Otherwise ask: "Work through this slice? `yes` / `no` / `skip-all`."
  - **yes** → invoke the `teach-me-changes` skill (`Skill` tool, `skill: "teach-me-changes"`), scope = this ticket (its diff, body, relevant PRD slice). When it returns, proceed to commit.
  - **no** → proceed to commit.
  - **skip-all** → set the batch flag (no more teach prompts this run), proceed to commit.

The teaching session does not commit anything itself — control returns here for the commit.

#### 3f. Commit

Use ticket title + id as commit subject. Example:
```
feat: {title} ({id})
```
Match repo's existing commit style — check `git log` first. Stage only files the subagent touched.

Never use `--no-verify`. If pre-commit hook fails, surface the error to user, do NOT amend, do NOT bypass.

### 4. Done

After last ticket: report summary — committed N, skipped M, aborted at K. Mention any uncommitted changes left in working tree.

### 5. Explain the batch

After the summary, hand the walkthrough to a subagent (skip if nothing was committed). Use `Agent` tool:
- `subagent_type: "general-purpose"`
- `model: "sonnet"`
- `prompt`: invoke the `explain-code` skill (`Skill` tool, `skill: "explain-code"`) and follow its format exactly. Scope = the cumulative diff `BASE_SHA..HEAD`; include `BASE_SHA` and the commit list in the prompt so the scope is unambiguous. The finished post is the final message.

Relay the subagent's post to the user verbatim — no summarizing, no rewriting.
