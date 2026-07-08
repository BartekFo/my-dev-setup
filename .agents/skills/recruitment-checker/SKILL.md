---
name: recruitment-checker
description: Analyze ConfigureFlow frontend recruitment submissions and produce a candidate feedback report.
---

# Skill: ConfigureFlow Recruitment Submission Checker

## Purpose

Analyze a candidate's submission for the **ConfigureFlow Frontend Recruitment Task v2** and produce a `candidates/{candidate_handle}/FEEDBACK.md` report. This is a **junior-level task** — the report decides whether to proceed to a live interview, not to grade code.

**Priority: Business Mindset > Communication > Work Discipline > Code**

Code can be taught. Prioritization, business thinking, and honest communication are much harder to develop.

---

## Input

The user provides a **public GitHub repo URL** (and optionally a branch name).

Examples:

```
Review this candidate: https://github.com/janedoe/configureflow-task
Review https://github.com/janedoe/configureflow-task on branch fix/critical-bugs
```

The template repo is: `https://github.com/masterborn/frontend-recruitment-task-v2`

> Throughout this document, `{handle}` refers to the candidate's GitHub username extracted from the repo URL.

---

## Single Source of Truth

The **template repo root** (this project — where the skill runs) is the authoritative reference for what the candidate was given. The candidate's cloned repo is only what we evaluate — never read task docs from it.

### Step 0 — Read the answer key

Read these files from the **template repo root** (this project's working directory):

| File                     | Contains                                                  |
| ------------------------ | --------------------------------------------------------- |
| `TICKETS.md`             | All tickets in the backlog (CFG-142 through CFG-157)      |
| `CONTEXT.md`             | Business context, terminology, architecture notes         |
| `README.md`              | The task instructions candidates received                 |
| `SUBMISSION_TEMPLATE.md` | The blank template — used to detect untouched submissions |

**Read these first.** You need them to:

- Compare the candidate's filled `SUBMISSION_TEMPLATE.md` against the blank original
- Verify ticket references and claimed bug descriptions against the actual tickets
- Check whether the candidate's questions are already answered in CONTEXT.md
- Understand the built-in tensions in the backlog — including the CFG-144 vs CFG-145 contradiction and the mismatch between CFG-152's Low label and its actual business importance

> These files are referred to as **"template docs"** throughout the prompts. Always read from the template repo root, never from the candidate's repo.

---

## Step 1 — Clone & extract

### 1a. Clone candidate repo

```bash
mkdir -p candidates/{handle}
git clone {url} candidates/{handle}/repo
```

### 1b. Identify working branch

```bash
cd candidates/{handle}/repo
git branch -r | grep -v HEAD
```

If user specified a branch, use that. Otherwise, pick the first non-`main`/`master` branch. If only `main` exists, use that. Checkout the branch.

### 1c. Extract candidate-only commits

```bash
cd candidates/{handle}/repo
FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD)
git log --format="commit %h%nAuthor: %an <%ae>%nDate:   %ai%n%n    %s%n" ${FIRST_COMMIT}..HEAD
```

Save to `candidates/{handle}/commits.txt`.

### 1d. File change summary + full diff

```bash
cd candidates/{handle}/repo
FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD)
git diff --stat ${FIRST_COMMIT}..HEAD > ../files_changed.txt
git diff ${FIRST_COMMIT}..HEAD > ../diff.txt
```

Save `files_changed.txt` and `diff.txt` to `candidates/{handle}/`.

### 1e. Check candidate's submission

Verify `candidates/{handle}/repo/SUBMISSION_TEMPLATE.md` exists and has been filled out. If the file doesn't exist or is unchanged from the blank template, note it — it's a major red flag.

---

## Step 2 — Run analysis passes

Read each prompt file from `prompts/` and the corresponding extracted data. Write intermediate findings to `candidates/{handle}/analysis_N.md`.

**Execute in this order:**

| Pass | Prompt                                 | Input data                                                                    | Evaluates                                                     |
| ---- | -------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------- |
| 1    | `prompts/01_business_mindset.md`       | `repo/SUBMISSION_TEMPLATE.md`, `files_changed.txt` + template docs (Step 0)   | Business mindset & communication (see prompt for criteria)    |
| 2    | `prompts/02_work_discipline.md`        | `commits.txt`, `diff.txt`, `files_changed.txt`, `repo/SUBMISSION_TEMPLATE.md` | Work discipline & code (see prompt for criteria)              |
| 3    | `prompts/03_technical_verification.md` | `diff.txt`, `files_changed.txt`, `repo/SUBMISSION_TEMPLATE.md`                | Technical fix quality, refactoring awareness, unicorn signals |

For each pass:

1. Read the prompt file — it contains detailed evaluation criteria
2. Read the specified extracted data files
3. Apply the criteria to the data
4. Write structured findings to `candidates/{handle}/analysis_N.md`

---

## Step 3 — Synthesize FEEDBACK.md

Read all `candidates/{handle}/analysis_1.md`, `analysis_2.md`, and `analysis_3.md`. Produce the final report using `FEEDBACK_TEMPLATE.md` as the structure guide. Write output to `candidates/{handle}/FEEDBACK.md`.

**Binary verdict only: PROCEED or REJECT.** No numeric scores.

### Hard-fail gate (check BEFORE deciding verdict)

Before writing the verdict, explicitly check each hard-fail signal from the list below against the analysis findings. If **any** hard-fail signal is present, the verdict is **REJECT** — regardless of how strong the candidate's technical work is. Strong code, good debugging narratives, or catching the CFG-144/145 contradiction do NOT override hard-fail signals. Document which hard-fail signal(s) triggered the REJECT in the Red Flags section.

Hard-fail signals:

- Empty or untouched submission
- Zero business context awareness (no mention of TechStyle, demo timeline, client impact, or compliance anywhere in the submission)
- Prioritizes cosmetic or low-impact work (e.g., dark mode, CSS polish, loading indicators) while critical bugs (crashes, data integrity, demo blockers) remain unaddressed — shows fundamental misalignment between effort and business impact
- Implementing CFG-144 or CFG-145 without providing reasoning for the choice
- Claims don't match actual work (significant discrepancies, not minor omissions)
- CFG-148 fixed with optional chaining (`?.`) instead of fixing the array mutation — patching the symptom on the highest-priority bug demonstrates a fundamental React misunderstanding that cannot be overlooked

Warning signals (flag in Red Flags section, but do NOT auto-reject):

- Single giant commit with no narrative — a junior may lack knowledge of commit discipline. Flag it as a growth area and probe in the interview, but don't reject on this alone.
- AI-generated submission with no codebase-specific language — flag for interview verification, do not reject on this alone.
- **CFG-149 loading indicator or CFG-158 memoization implemented in a way that masks the `$0.00` symptom of CFG-142 without fixing the underlying unit mismatch.** The candidate shipped a change that hides the bug rather than resolving it. Junior candidates plausibly fall for this — it's a growth-area signal and an interview probe, not a REJECT.
- **Blind implementation of label-mismatched tickets** — e.g., candidate implemented CFG-158 (labeled High but low real impact) uncritically, or skipped CFG-152 (labeled Low but compliance-sensitive) without reasoning. Note as label-discernment gap.

---

## Verdict Criteria

### PROCEED — schedule interview

Candidate demonstrates business mindset and communication ability. See prompt files for detailed criteria.

### REJECT — any of these hard-fail signals

- Empty or untouched submission
- Zero business context awareness
- Prioritizes cosmetic or low-impact work (dark mode, CSS polish, loading indicators) over critical bugs (crashes, data integrity, demo blockers)
- Implementing CFG-144 or CFG-145 without providing reasoning for the choice — demonstrates blind order-taking without critical thinking. CFG-144 is a product decision to remove a feature; CFG-145 is a customer request to improve that same feature. Implementing either without reasoning shows the candidate doesn't read the backlog holistically.
- Claims don't match actual work (significant discrepancies, not minor omissions)
- CFG-148 fixed with optional chaining instead of fixing the mutation — symptom patch on the highest-priority bug

> **Note:** A single giant commit with no narrative is a concern worth flagging but not a hard-fail for a junior role. Commit discipline can be taught. Always note it in the report and suggest it as an interview topic.

## Label-vs-Description Discernment (Pass 1 input)

The v2 backlog intentionally contains tickets whose priority label does not match the real business priority:

| Ticket                  | Label   | Reality                                                                                      |
| ----------------------- | ------- | -------------------------------------------------------------------------------------------- |
| CFG-152 (keyboard nav)  | ⚪ Low  | Actually compliance-sensitive (WCAG 2.1 AA is in TechStyle MSA) — higher real priority       |
| CFG-158 (memoize props) | 🟠 High | Low real impact, and the suggested fix is a planted trap (breaks URL-decoded initial config) |

When evaluating Pass 1, check SUBMISSION_TEMPLATE's "Tickets With a Misleading Priority Label" section:

- Candidate flagged ≥2 mismatches with reasoning → strong label-discernment signal
- Candidate flagged 1 with reasoning → partial
- Candidate flagged none / blindly followed labels → weak (note as growth area)

This complements — does NOT replace — prioritization reasoning in Pass 1.

---

## Evaluation Philosophy

**Priority: Business Mindset > Communication > Work Discipline > Code.** Code can be taught; prioritization, business thinking, and honest communication are much harder to develop. The prompt files define all detailed criteria — this section only sets the lens. What matters less: number of tickets completed, specific framework knowledge, CSS perfection, or whether the app runs flawlessly.

No single signal should dominate the verdict. Evaluate the full picture — prioritization reasoning, business awareness, explanation depth, and self-awareness should all contribute. A candidate who aces one criterion but shows weakness across the rest is not a PROCEED. Conversely, consistent strength across multiple criteria is more valuable than a single standout moment.
