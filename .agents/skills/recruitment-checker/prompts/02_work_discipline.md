# Pass 2: Work Discipline & Code

## Purpose

Evaluate how the candidate works — their process, honesty, and technical foundations. This pass supports the verdict from Pass 1 but rarely overrides it.

## Input Data

- `candidates/{handle}/commits.txt` — candidate's commit history
- `candidates/{handle}/diff.txt` — full diff of all changes
- `candidates/{handle}/files_changed.txt` — summary of changed files
- `candidates/{handle}/repo/SUBMISSION_TEMPLATE.md` — the candidate's submission (for cross-checking claims)

## Evaluation Criteria

### 1. Commit Narrative

Do the commits tell a chronological story of the work session?

Strong:
- Logical progression (triage first, then fixes in priority order)
- Atomic commits (one concern per commit)
- Messages describe the intent, not just the action ("fix crash on deselect" > "fix bug")
- Timestamps show a structured work session

Weak:
- Single monolithic commit ("completed task", "done", "all fixes")
- Messages that don't convey meaning ("update", "fix", "wip")
- Commits that mix unrelated changes
- Evidence of squashing or rewriting to hide the actual process

Warning (flag, not auto-reject):
- A single commit with everything is a concern — note it in the report and suggest as an interview topic. For a junior role, this reflects a knowledge gap, not a mindset problem.

### 2. Claims vs Reality

Cross-check the candidate's submission claims against `files_changed.txt` and `diff.txt`:

- Do they claim to fix tickets that aren't reflected in the code?
- Do they describe changes to files that weren't actually modified?
- Are there significant code changes they didn't mention in the submission?
- Does the scope of changes match what they described?

Discrepancies aren't necessarily disqualifying — but significant gaps between claims and reality are a red flag.

### 3. Fix Quality

For each bug fix in the diff, assess whether it addresses root cause or symptoms:

**Root cause examples** (strong):
- Proper debounce/throttle for rapid input issues (CFG-142)
- Correct dependency management (CFG-148 crash on deselect)
- Proper URL encoding for share links (CFG-147)
- Cleanup functions for subscriptions/timers (CFG-143 memory leak)

**Symptom patches** (weak):
- setTimeout/delay hacks instead of proper debounce
- try/catch wrapping instead of fixing the error source
- Disabling features instead of fixing them
- Ignoring the error instead of handling the condition

Note: For a junior role, symptom patches aren't disqualifying — but recognizing the difference in their write-up shows growth potential.

### 4. Code Observations

Light-touch review — this is a junior role, not a senior code audit:

- **New bugs introduced?** — Did any fix create a new problem?
- **React fundamentals** — Proper hook usage? Key props on lists? Effect cleanup? (Observe, don't penalize)
- **Cleanup thoroughness** — Did they leave debug logs, commented code, or TODO markers?
- **Code style** — Consistent with the existing codebase? Or did they reformat everything?

### 5. Growth Tips

**Always generate 2-3 tips, regardless of verdict.** These should be:
- Kind and encouraging in tone
- Specific to what you observed in their code (not generic advice)
- Actionable — something they can apply immediately
- Junior-appropriate — fundamentals, not advanced patterns

Examples:
- "Your fix for CFG-142 uses setTimeout — look into lodash's debounce or a custom hook for a more robust approach to rapid user input."
- "Great instinct fixing the crash first! Next time, try adding a brief note in your commit message about WHY this was the priority."
- "You cleaned up the console warnings nicely. Consider also removing the commented-out code blocks you left in ProductConfigurator.tsx."

## Output Format

Write to `candidates/{handle}/analysis_2.md`:

```markdown
# Analysis 2: Work Discipline & Code

## Commit Narrative
**Commits**: [N] over [timespan]
[Assessment of commit quality and story they tell]

## Claims vs Reality
[Cross-check results — matches, gaps, discrepancies]

## Fix Quality
[For each fix: root cause or symptom patch? Brief assessment]

## Code Observations
[Light-touch notes on code quality, new bugs, React fundamentals]

## Growth Tips
1. [Specific, kind, actionable tip]
2. [Specific, kind, actionable tip]
3. [Specific, kind, actionable tip]

## Pass 2 Summary
[2-3 sentence overall assessment of work discipline]
```
