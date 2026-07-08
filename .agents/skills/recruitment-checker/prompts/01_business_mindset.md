# Pass 1: Business Mindset & Communication

## Purpose

Evaluate whether the candidate thinks like someone who understands WHY they're doing the work, not just HOW. This is the most important pass — it drives the verdict.

## Input Data

- `candidates/{handle}/repo/SUBMISSION_TEMPLATE.md` — the candidate's filled-out submission
- `candidates/{handle}/files_changed.txt` — summary of all changed files
- **Template docs** (from template repo root — the single source of truth): `TICKETS.md`, `CONTEXT.md`, `SUBMISSION_TEMPLATE.md`. Always read these from the template repo root, never from the candidate's repo.

## Evaluation Criteria

> **Holistic evaluation**: No single criterion should dominate the verdict. A PROCEED requires strength across the top 3-4 criteria below. A standout performance on one criterion does not compensate for weakness everywhere else — evaluate the full picture before deciding.

### 1. Prioritization Reasoning

This is the **core competency being tested**. The backlog contains 16 tickets but the candidate has only ~4 hours. The TechStyle demo is 2 weeks away. What matters is the WHY behind their choices, not the WHAT.

Strong signals:
- Crash bugs first (CFG-148, CFG-142) because they block the demo
- Recognizes CFG-153 ("Compare Configurations") lacks proper scoping — the ticket only has a vague note ("Estimate was 2-3 weeks. Not sure why it's in this sprint.") with no detailed requirements. Raising this as a question or clarification is a stronger signal than simply skipping it based on the note.
- Business-driven reasoning ("demo blocker", "users can't complete purchases")
- Recognizes ticket labels may not reflect true priority (e.g., CFG-152 is labeled Low but tied to compliance — see Criterion 2)

Weak signals:
- Purely technical reasoning ("this was an easy fix")
- Random ordering with no rationale
- Attempting CFG-153 without acknowledging the missing scope — the ticket has minimal acceptance criteria and an informal estimate; diving in without questioning it suggests the candidate doesn't evaluate scope before committing effort
- Prioritizes cosmetic or low-impact tickets (CFG-155 dark mode, CFG-150 CSS alignment, CFG-149 loading indicator) while crash bugs (CFG-148) or data bugs (CFG-142) remain unaddressed

**CFG-144/145 handling** (contradiction sub-signal):
CFG-144 says "remove Quick Add feature" while CFG-145 says "improve Quick Add with keyboard shortcut." They directly contradict each other — one is a product decision to remove a feature, the other is a customer request to improve that same feature.

If the candidate worked on either ticket, check whether they provided reasoning:
- **Caught** — explicitly noted the conflict, explained their decision (strong positive)
- **Implicit** — chose one without mentioning the conflict, but provided sound reasoning for the choice
- **No reasoning** — implemented CFG-144 or CFG-145 (or both) without any reasoning or acknowledgment of the contradiction (red flag — shows blind order-taking without critical thinking)
- **Not addressed** — didn't work on either ticket (neutral — evaluate other signals)

### 2. Business Awareness

Does the candidate connect their work to the business context?

#### Tier 1 — Demo timeline & compliance
- References the TechStyle demo and its 2-week deadline as a driver for prioritization
- Recognizes CFG-152 as a WCAG/contractual concern — CONTEXT.md states TechStyle has WCAG 2.1 AA compliance requirements, and the ticket itself notes it "should probably be prioritized higher." A candidate who connects keyboard navigation to compliance risk, legal exposure, or contractual obligation demonstrates business thinking beyond pure UX empathy.
- Frames priorities in terms of "what blocks the demo" or "what risks the deal"

#### Tier 2 — Client/user impact
- Mentions client impact, user experience consequences, or business outcomes beyond just technical severity
- Connects bug fixes to user workflows or demo scenarios

#### Tier 3 — General
- Uses business language anywhere in their submission
- Shows awareness this is a real product scenario, not just a coding exercise

> **Note on CFG-152**: Many strong candidates will reasonably prioritize crash bugs over accessibility. Credit the CFG-152 compliance connection when present — do not treat its absence as a gap.

### 3. Explanation Depth

For each issue they worked on, assess their write-up:

Strong:
- Describes the debugging process("opened devtools, noticed X, suspected Y, confirmed by Z")
- Identifies root cause, not just symptoms
- Mentions alternatives considered and why they chose their approach
- Uses codebase-specific language (component names, hook names, state variables)

Weak:
- Only describes the fix, not how they found the problem
- Generic descriptions that could apply to any codebase
- No mention of why their approach was chosen over alternatives

### 4. Self-Awareness

Check their self-assessment section:

Strong:
- Specific challenges described ("I struggled with the pricing calculation because...")
- Honest about what they didn't finish and why
- Concrete "what I'd do differently" reflections
- Acknowledges knowledge gaps without being defensive

Weak:
- Claims everything went perfectly
- Generic reflections ("I would spend more time testing")
- No specific challenges mentioned
- Defensive tone about gaps

### 5a. Label-vs-Description Discernment

The v2 backlog intentionally contains tickets where the priority label does not match real business priority:

- **CFG-152 keyboard navigation** — labeled ⚪ Low, but tied to WCAG 2.1 AA (TechStyle MSA compliance clause). Real priority is higher than the label suggests.
- **CFG-158 memoize props** — labeled 🟠 High with Marcus's suggested fix, but the fix is a trap (breaks URL-decoded initial config) and the real performance impact is minimal.

Check the candidate's SUBMISSION "Tickets With a Misleading Priority Label" section (and their prioritization write-up):

- **Strong** — flagged ≥2 mismatches with reasoning rooted in the description or business context
- **Partial** — flagged 1 with reasoning
- **Weak** — blindly followed labels (e.g., skipped CFG-152 because it's labeled Low, or implemented CFG-158 uncritically because it's labeled High)

This complements Prioritization Reasoning but doesn't replace it. A candidate who blindly follows labels AND lacks business reasoning is a REJECT-level concern; a candidate who flags one mismatch but otherwise reasons well is still PROCEED-eligible.

### 5b. Ask, Don't Fix — on ambiguous tickets

Some tickets are intentionally ambiguous. A senior instinct is to stop and escalate rather than guess.

Applies to:
- **CFG-154 (🧪 Unclear)** — two contradictory narratives, strict `>` in code but UI label says "50+". Financial risk in both directions (over-discount vs. under-discount).
- **CFG-153 (unscoped)** — informal estimate, no acceptance criteria.

Check the candidate's SUBMISSION "Tickets Where You Stopped to Ask Instead of Implementing" section:

- **Strong** — explicitly refused to implement, named the escalation target (PM / Finance / Design), quantified the business risk
- **Medium** — implemented but noted the uncertainty and what they assumed
- **Weak** — implemented blind with no acknowledgment of ambiguity

### 6. Questions Quality

Check their "Questions for the Team" section:

Strong:
- Business-relevant questions (about users, the demo, product direction)
- Questions that show they read and engaged with CONTEXT.md
- Specific technical questions that require team context to answer

Weak:
- Questions already answered in CONTEXT.md (they didn't read it)
- No questions at all
- Only generic questions ("what's the tech stack?")

### 6. Growth Tips (Business & Communication)

**Always generate 2-3 tips, regardless of verdict.** These should focus on business mindset and communication — not code. They should be:
- Kind and encouraging in tone
- Specific to what you observed in their submission (not generic advice)
- Actionable — something they can apply in their next project or interview
- Focused on prioritization, stakeholder communication, business reasoning, or self-assessment

Examples:
- "Your triage was technically sound but didn't mention the TechStyle demo deadline — try framing priorities in terms of business impact next time."
- "Great instinct flagging the contradiction! To strengthen it further, briefly state what you'd ask the PM before deciding."
- "Your self-assessment was honest but generic. Try naming the specific moment you got stuck and what you tried before switching approach."

### 7. AI-Assisted Submissions

AI usage is acceptable and not penalized — company policy allows it, and the tech interview is where genuine understanding is tested.

If signs of heavy AI generation are observed, note them as a **suggested interview angle** — not a concern or red flag:
- Generic phrasing with no codebase-specific detail (component names, hook names, state variables)
- No personal debugging narrative or specific struggles
- Suspiciously uniform writing quality with no personality
- Uses filler phrases like "I leveraged", "comprehensive solution", "robust approach"

When noted, provide concrete probing questions for the interviewer:
- "Walk me through your debugging process for [specific ticket they claimed to fix]."
- "What did you try before arriving at that approach for [specific fix]?"
- "Can you explain what [specific component/hook from their diff] does and why your change works?"

## Output Format

Write to `candidates/{handle}/analysis_1.md`:

```markdown
# Analysis 1: Business Mindset & Communication

## Prioritization
[Assessment with evidence. Include CFG-144/145 contradiction handling here — classify as Caught/Implicit/No reasoning/Not addressed with evidence and quotes from submission.]

## Business Awareness
[Assessment — did they connect to TechStyle demo, client impact? Note if they recognized CFG-152's compliance angle. Reference tier level.]

## Label-vs-Description Discernment
[Strong / Partial / Weak. Quote from SUBMISSION's "Misleading Priority Label" section. Note which mismatches they caught (CFG-152, CFG-158).]

## Ask-Don't-Fix (CFG-154, CFG-153)
[Strong / Medium / Weak / Not addressed. Quote from SUBMISSION's "Stopped to Ask" section or prioritization write-up.]

## Explanation Depth
[Assessment with examples from their write-ups]

## Self-Awareness
[Assessment — genuine reflection or surface-level?]

## Questions Quality
[Assessment of their team questions]

## Growth Tips (Business & Communication)
1. [Specific, kind, actionable tip on prioritization, communication, or business reasoning]
2. [Specific, kind, actionable tip on prioritization, communication, or business reasoning]
3. [Specific, kind, actionable tip on prioritization, communication, or business reasoning]

## AI-Assisted Submission Notes
[If indicators of heavy AI generation are present, note suggested interview questions. Otherwise write "No indicators noted."]

## Pass 1 Summary
[2-3 sentence overall assessment of business mindset signals]
```
