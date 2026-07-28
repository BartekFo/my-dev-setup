---
name: ship-tickets
description: Ship a batch of pre-written tickets serially — implementation via the `implement` skill and review via `code-review`, both executed by subagents on explicit model tiers, with a human gate before every commit.
disable-model-invocation: true
---

# Ship Tickets

Serial, human-gated shipping of a ticket batch. The main thread **orchestrates only** — never writes code itself. Per ticket, one at a time (never parallel): implement (subagent driving the `implement` skill) → code review (`code-review` skill) + auto-fix → human gate → commit. On approve, optionally work through the slice with `teach-me-changes` first. After the batch, a subagent writes the walkthrough via the `explain-code` skill.

Machine-facing subagent reports use compact, Cavecrew-inspired protocols to protect the main context. Compression applies to wording, never evidence: retain changed paths, exact verification commands, acceptance-criterion results, finding locations, severity, sources, and fixes. Human-facing gates remain normal prose.

## Inputs

User invokes: `/ship-tickets <path>`

`<path>` resolves to one of:
- Directory containing `*.md` ticket files
- Single markdown file listing multiple tickets
- File with newline-separated issue tracker refs (URLs or IDs) — fetch each via the issue tracker

If `<path>` missing or unreadable, ask user for it. Otherwise no further questions — proceed.

## Model tiers

Dispatch every subagent with an explicit model. An omitted model inherits the session's — usually the most capable and most expensive available.

Name **tiers**, never vendors, so this skill runs on any harness. Resolve each tier to the cheapest model of that class the current harness offers:

| Tier | Class | Dispatched for |
|---|---|---|
| `fast` | cheapest usable coding model | the tweak applier (3g); the implementer on a `no-test` ticket |
| `standard` | mid-tier workhorse | the implementer (default); both review axes; the walkthrough |
| `deep` | most capable available | the implementer when a ticket spans 3+ modules or turns on a design decision |

`standard` is the floor for reviewers and for any implementer working from prose: a cheaper model takes more turns on the same diff and costs more end to end.

The implementer's tier is a pre-dispatch guess from the ticket text. The subagent's own `mode:` classification arrives only in its report — use it for review depth (3b), not to second-guess the tier already spent.

## Workflow

### 1. Load tickets

Read every ticket. For each capture: `id` (filename or tracker id), `title`, `body`, `acceptance criteria`, `blocked by`.

### 2. Open the ledger and sort

Topologically sort tickets using `Blocked by`. Detect cycles → stop, report to user.

**One ticket:** there is no order to show — skip straight to the ledger.

Otherwise show the planned order as a numbered list (title + id only), then continue immediately with the first ticket. The order is informational: do not wait for "go" or approval. The user may still interrupt to reorder or skip tickets. The first mandatory pause is the code-review gate in step 3c.

**The ledger.** Main-thread memory does not survive compaction, and a batch outlives it. A controller that loses its place re-ships tickets already committed. Track position in a file.

The ledger is scratch, so it lives outside the repo — same convention as `teach-me-changes` and `visual-plan`. Nothing to gitignore, nothing that can be committed by accident:

```
${TMPDIR:-/tmp}/ship-tickets/<repo-name>/<batch-slug>.md
```

`<repo-name>` is the basename of `git rev-parse --show-toplevel`, `<batch-slug>` derives from `<path>` — together they make the path reproducible, so a resumed run finds its own ledger without being told where it is.

Open it with its identity and baseline:

```
# ship-tickets — batch: docs/tickets/auth/
BASE_SHA: 4f2a1bc
```

`BASE_SHA` is `git rev-parse HEAD` before the first ticket; step 5 scopes the walkthrough to it.

If the ledger already exists and its first line names **this** batch, every ticket carrying a `committed`, `skipped`, or `aborted` line is done — resume at the first ticket without one, and reuse the recorded `BASE_SHA`. A ledger naming a different batch belongs to another run: leave it, open your own.

Temp directories get swept. A missing ledger means a fresh start, which is safe rather than silent: reconcile against `git log` before the first dispatch and tell the user which tickets already appear as commits.

From here the ledger and `git log` outrank recollection.

### 3. Loop per ticket

#### 3a. Implement (subagent)

Use the `Agent` tool. Required params:

- **Implementer rules** — on a harness carrying the `ticket-implementer` agent definition, pass `subagent_type: "ticket-implementer"`; it already holds the standing rules. Elsewhere dispatch a general-purpose subagent and point it at `implementer.md` in this skill's directory — same rules, same report protocol.
- `model` — the tier from **Model tiers**, always explicit.
- `description` — short 3-5 word task name.
- `prompt` — self-contained ticket brief (template below).

Every ticket goes through a subagent; the main thread orchestrates. One-sentence corrections have their own path at 3g, and only once the human has seen the diff.

<subagent-prompt-template>
Implement this ticket. Follow your standing rules: drive the work through the `implement` skill, no commit, no self-review, run lint/typecheck/tests, and return only your compact standard report.

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

After the subagent returns, before surfacing to the user, review via the `code-review` skill. Four adaptations for this loop:

- **Fixed point = `HEAD`.** The implement subagent did not commit, so the diff under review is the working tree: point the axis sub-agents at `git diff HEAD` plus untracked files — not `<fixed-point>...HEAD`. The non-empty check runs against that working-tree diff.
- **Spec source = the ticket.** Pass `{body}` + acceptance criteria straight to the Spec sub-agent — skip the skill's commit-message / issue-tracker hunt.
- **Model.** Both axis sub-agents get the `standard` tier.
- **Depth follows the implementer's `mode:`.** `tdd` and `safety-net` get both axes. `no-test` (docs, config, formatting, lockfiles) gets Spec alone — that diff has no behaviour for Standards to judge.

Then:

1. Collect findings from the axes that ran.
   - **No findings** → skip straight to 3c.
   - **Findings exist** → re-dispatch the implementer (same params as 3a) with the finding lines in the feedback slot; omit `No issues.` and `totals:` lines. Instruct it to apply the fixes (Spec gaps and hard Standards violations first; baseline smells are judgement calls), no commit, re-run lint/typecheck/tests.
2. One review + one fix pass is enough. Do not loop the review — the human gate in 3c catches anything left. (`reject` in 3d returns here, so re-reviews happen on demand.)
3. Fixes are orchestrate-only too — the subagent applies them.

#### 3c. Surface diff to user

After review + fixes:
- Run `git status` + `git diff` to confirm actual changes (subagent summary ≠ truth — verify).
- Translate the compact machine reports into a concise, normal-language summary: ticket id, files changed, subagent test/lint results, and what each review axis that ran flagged + what was fixed. Do not paste the protocols verbatim.
- Explicitly state: "Awaiting code review. Reply `approve` to commit + continue, `tweak <one-sentence fix>` for a small correction, `reject <feedback>` to revise properly, `skip` to move on without commit, or `pause` to stop and resume later."

STOP HERE. Do not continue to next ticket. Do not auto-commit. Wait for user reply.

#### 3d. On user response

- **approve** → teach gate (3e) → commit (3f) → next ticket.
- **tweak `<instruction>`** → fast path (3g) → surface again (3c).
- **reject `<feedback>`** → re-dispatch the implementer with the feedback appended to the prompt, then return to 3b (re-review + re-fix, then surface again).
- **skip** → leave changes as-is (or ask the user whether to revert them). Ledger `skipped`, move to next ticket.
- **pause** → ledger the position, leave the working tree untouched, stop the loop, and tell the user that re-running `/ship-tickets <path>` resumes here.
- **abort** → ledger `aborted`, stop the whole loop.

#### 3e. Teach gate (opt-in)

After `approve`, before committing, offer to work through what was just built — while the slice is small and fresh.

- If the batch `skip-all` flag is set, skip this step entirely.
- Otherwise ask: "Work through this slice? `yes` / `no` / `skip-all`."
  - **yes** → invoke the `teach-me-changes` skill, scope = this ticket (its diff, body, relevant PRD slice). When it returns, proceed to commit.
  - **no** → proceed to commit.
  - **skip-all** → set the batch flag (no more teach prompts this run), proceed to commit.

The teaching session does not commit anything itself — control returns here for the commit.

#### 3f. Commit

Subject = ticket title + id. Body = short description of what changed and why — drawn from the actual diff and the ticket, not the subagent's report. Example:
```
feat: {title} ({id})

{2-4 sentences: what changed, why, anything a future reader needs}
```
Match repo's existing commit style — check `git log` first. Stage only files the subagent touched.

Never use `--no-verify`. If pre-commit hook fails, surface the error to user, do NOT amend, do NOT bypass.

Then append one ledger line, tweaks noted in parentheses:

```
T-101 add login form: committed 4f2a1bc..9d3e7aa (1 tweak)
```

#### 3g. Tweak (fast path)

`tweak` carries corrections the user can state completely in one sentence — a rename, a moved line, a changed constant, a copy fix. The instruction *is* the spec, so a review pass would only re-derive what the user already said, and the gate at 3c is about to see the result anyway.

Dispatch one `fast`-tier subagent with the instruction verbatim, the paths it may touch, and the brief: apply exactly this, change nothing else, no commit. On return, run only the targeted checks — the test file covering the touched code, plus typecheck — never the full suite. Then go straight back to 3c.

When the instruction turns out to need judgement, new tests, or more than one file, the subagent reports back without editing and the user routes it through `reject` instead.

### 4. Done

After the last ticket, read the ledger and report: committed N, skipped M, paused or aborted at K. Mention any uncommitted changes left in the working tree.

### 5. Explain the batch

Skip when nothing was committed. When exactly one ticket was committed, ask before dispatching — the user reviewed that same diff minutes ago at the gate.

Otherwise hand the walkthrough to a subagent (`Agent` tool):
- a general-purpose subagent
- `model`: `standard` tier
- `prompt`: invoke the `explain-code` skill and follow its format exactly. Scope = the cumulative diff `BASE_SHA..HEAD`, taking `BASE_SHA` from the ledger; include it and the commit list in the prompt so the scope is unambiguous. The finished post is the final message.

Relay the subagent's post to the user verbatim — no summarizing, no rewriting. Compact reporting does not apply here: `explain-code` is deliberately human-facing prose.

Then delete the batch ledger — git history is the record now.
