# Recruitment Checker — Usage

## Quick start

In Claude Code, from the repo root:

```
Review this candidate: https://github.com/gabpie2/masterborn-frontend-recruitment-task-v2
```

Or via slash command:

```
/recruitment-checker https://github.com/gabpie2/masterborn-frontend-recruitment-task-v2
```

## What it does

1. Clones the candidate's repo into `candidates/{handle}/`
2. Extracts commits, diffs, and file changes
3. Runs 3 analysis passes:
   - **Pass 1** — Business mindset & communication (prioritization, business awareness, explanation depth, self-awareness)
   - **Pass 2** — Work discipline & code (commit quality, fix quality)
   - **Pass 3** — Technical verification (root cause vs symptom per ticket, refactoring awareness, unicorn signals)
4. Produces `candidates/{handle}/FEEDBACK.md` with a **PROCEED** or **REJECT** verdict

## Output

```
candidates/{handle}/
├── repo/                # cloned submission
├── commits.txt          # candidate-only commit log
├── files_changed.txt    # diff --stat summary
├── diff.txt             # full diff
├── analysis_1.md        # Pass 1 findings
├── analysis_2.md        # Pass 2 findings
├── analysis_3.md        # Pass 3 findings
└── FEEDBACK.md          # final verdict + interview questions
```

## Evaluation priority

**Business Mindset > Communication > Work Discipline > Code**

No single signal dominates — the verdict weighs the full picture across criteria.

## Key files

| File | Purpose |
|------|---------|
| `SKILL.md` | Full skill spec — steps, verdict criteria, hard-fail signals |
| `prompts/01_business_mindset.md` | Pass 1 evaluation criteria |
| `prompts/02_work_discipline.md` | Pass 2 evaluation criteria |
| `prompts/03_technical_verification.md` | Pass 3 evaluation criteria |
| `FEEDBACK_TEMPLATE.md` | Structure for the final report |
