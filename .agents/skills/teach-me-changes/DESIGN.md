# Design: teach-me-changes

Date: 2026-06-03

## Problem

The user runs an AFK-ish flow: story → `/grill-with-docs` → `/to-prd` → `/to-issues` → `/implement-issues`. Agents (Sonnet subagents) write most of the code. The user ends up with merged changes they did not write and may not deeply understand — the "I shipped it but can't explain it" gap.

A teaching prompt (the "wise teacher" prompt) closes this gap: it verifies the *human* deeply understands what was built — the problem, the solution, design decisions, edge cases, and broader impact — via incremental explanation and quizzing.

## Goal

Turn that teaching prompt into a reusable skill and wire it into the existing flow so the human learns each change on the spot, while context is small and fresh.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Placement | Woven into `/implement-issues`, per-issue |
| Position in loop | After human code-review gate, **before commit** |
| Trigger | **Opt-in per issue** (ask: yes / no / skip-all) |
| Learning artifact | **Ephemeral** md checklist (e.g. `/tmp`), not committed |
| Language | Gender-neutral (2nd person "you" / "the learner") — no "she/her" |
| Skill name | `teach-me-changes` |
| Structure | Standalone skill file, invoked from inside the implement-issues loop (keeps implement-issues lean; also runnable manually) |

## Architecture

```
~/.claude/skills/teach-me-changes/SKILL.md   ← new skill (the teaching engine)
~/.claude/skills/implement-issues/SKILL.md   ← edited: add opt-in gate that invokes it
```

### Integration point (implement-issues, step 3, per issue)

```
implement → code review → human gate (approve)
  → [NEW] ask: "Work through this slice?" (yes / no / skip-all)
       yes      → invoke teach-me-changes (scope = this issue)
       no       → continue
       skip-all → set batch flag, stop asking for the rest of the run
  → commit
  → next issue
```

`skip-all` sets a per-run flag so no further prompts appear in this batch.

## Teaching engine (teach-me-changes)

**Input scope:** one issue — its diff (this slice), the issue body, and the relevant PRD slice. When run manually: optional arg (issue ref / diff range); default = HEAD / last commit.

**Behavior (from the original prompt, gender-neutral):**

1. **Ephemeral checklist** at `/tmp/teach-<issue-id>.md` (not committed, dies with the session). Three blocks:
   - The problem, why it existed, the branches considered.
   - The solution, why resolved this way, the design decisions, the edge cases.
   - The broader context: why it matters, what the changes impact.
2. **Learner restates first** — ask the human to state their current understanding in their own words, *then* fill gaps from there.
3. **Incremental** — do not advance to the next block until the current one is mastered. Learner may request `eli5` / `eli14` / `elii` (explain like an intern).
4. **Drill the whys** — make sure the human understands why (and deeper whys), plus what and how.
5. **Quiz via `AskUserQuestion`** — open-ended or multiple-choice; randomize the position of the correct answer; do not reveal answers until after submission. Show code or have the learner use the debugger when useful.
6. **Exit gate** — the session does not end until every checklist item is demonstrated. Then control returns to implement-issues, which commits.

## Edge cases

- **`skip-all`** mid-batch → remaining issues commit with no prompt.
- **Empty / trivial diff** → skill reports "nothing to teach" and returns immediately.
- **Manual invocation** outside the loop → accepts optional issue ref / diff range; no arg → HEAD.
- **Learner stuck on an item** → keep explaining (eli5/eli14/elii), do not skip the gate.

## Out of scope (YAGNI)

- No persisted/committed learning logs.
- No changes to `/to-issues` (no new label needed — trigger is interactive, not label-driven).
- No grading/scoring persistence beyond the ephemeral checklist.
