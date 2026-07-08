# FEEDBACK_TEMPLATE.md — Final Report Structure

Use this structure when synthesizing all analysis passes into the final `FEEDBACK.md`.

---

```markdown
# Submission Review: {candidate_handle}

> Reviewed: {date} | Branch: {branch} | Commits: {N} over {timespan}

---

## Verdict: [PROCEED / REJECT]

**One-line**: [Decisive signal in one sentence]

---

## Business Mindset & Communication

### Prioritization
[Assessment and evidence]

### Business Awareness
[Assessment and evidence]

### Explanation Quality
[Assessment and evidence]

### Self-Awareness
[Assessment and evidence]

### Growth Tips (Business & Communication)
[Always included — 2-3 kind, specific, actionable suggestions on prioritization, communication, or business reasoning regardless of verdict.]

- [Tip 1]
- [Tip 2]
- [Tip 3]

---

## Work Discipline & Code

### Commit Narrative
[Do commits tell a chronological story of the work session? Or single dump?]

### Fix Quality
[Root cause fixes vs symptom patches? Proper debounce vs setTimeout? Correct encoding vs try/catch?]

### Growth Tips
[Always included — 2-3 kind, specific, actionable suggestions regardless of verdict.]

- [Tip 1]
- [Tip 2]
- [Tip 3]

---

## Technical Verification

### CFG-148
[Root cause fix (filter) / symptom patch (optional chaining) / not attempted. If symptom patch: **HARD-FAIL SIGNAL**.]

### CFG-142
[Root cause fix / symptom patch / not attempted. Note if candidate correctly identified unit mismatch (Date.now() vs requestCounter) vs generic "race condition" label.]

### CFG-143 & Other Fixes
[Resize handler cleanup: present / missing. Brief note on CFG-147, CFG-154, CFG-156 if attempted.]

### Refactoring Awareness
[Mentioned 1000-line component / extracted a component / justified skipping / not mentioned at all.]

### Growth Tips (Technical)
[Always included — 2-3 kind, specific, actionable tips on code quality, React fundamentals, or debugging approach.]

- [Tip 1]
- [Tip 2]
- [Tip 3]

---

## Unicorn Signals

> **Omit this section entirely if none were observed.**

[List each signal: tests added, CFG-152 with compliance reasoning, undocumented bug found, component extracted, architecture proposal, conventional commits.]

---

## Suggested Interview Questions (PROCEED only)

> **If AI-assisted submission indicators were noted in Pass 1**, include at least one question that probes authentic understanding of specific work claimed.

[3-5 questions grounded in the ConfigureFlow task but probing deeper than the submission. Don't ask "why did you pick ticket X?" — that's already in their write-up. Instead, twist the scenario, shift constraints, or zoom out to SDLC thinking. All questions must reference the task context (ProductConfigurator, TechStyle, Marcus, the specific tickets). Mix from these angles:]

**Scenario twists** — same codebase, different constraints:
- "QA finds your CFG-142 fix breaks bulk ordering 30 minutes before the TechStyle demo. What's your next move — and who do you talk to first?"
- "TechStyle's PM asks you to add CFG-153 (Compare Configurations) to the demo scope. How do you push back — or do you?"

**SDLC & process** — how they'd work on the ProductConfigurator in a real team:
- "You're handing off the ProductConfigurator to a new dev. Marcus left nothing. What do you document first and what format do you use?"
- "You spot CFG-144 and CFG-145 contradicting each other mid-sprint. Walk me through what happens before you write any code."

**Mindset & judgment** — abstract but tied to the task:
- "The ProductConfigurator has 14 open tickets and a demo in 2 weeks. How do you decide what 'done enough' looks like?"
- "You fixed CFG-148 with a quick guard clause. When does a fix like that become tech debt, and how would you flag it?"

**Submission springboards** — use their specific choices as a jumping-off point:
- "You [specific choice from submission]. If the TechStyle demo got pushed back a month, would you change that decision? Why?"
- "You skipped [ticket they deprioritized]. The client emails asking about it the day after the demo. Draft your reply out loud."

1. **[Angle]**: [Question] — *[what it reveals]*
2. **[Angle]**: [Question] — *[what it reveals]*
3. **[Angle]**: [Question] — *[what it reveals]*
4. **[Angle]**: [Question] — *[what it reveals]*
5. **[Angle]**: [Question] — *[what it reveals]*

---

## Red Flags (if any)

[Only include this section if there are specific red flags to call out. Otherwise omit entirely.]
```
