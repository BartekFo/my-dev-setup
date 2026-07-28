---
name: receiving-code-review
description: Use when receiving code review feedback, before implementing any suggestion — each item gets a verdict (implement, push back, or clarify) backed by codebase evidence, not performative agreement.
---

# Receiving Code Review

Review feedback is a set of claims to verify, not orders to follow. Every item gets a **verdict** — implement, push back, or clarify — and every verdict is backed by codebase evidence.

## Process

1. **Read** the complete feedback before reacting to any item.
2. **Clarify.** If any item is unclear, stop and ask about all unclear items before implementing anything — items may be related, and partial understanding produces wrong implementations. Done when: you can restate every item in your own words.
3. **Verify** each item against the codebase:
   - Does the claim hold for this codebase, stack, and supported platforms/versions?
   - Does the suggestion break existing functionality? Reference working code and tests.
   - Is there a reason for the current implementation (compatibility, legacy, a prior architectural decision)?
   - For "implement this properly" suggestions: grep for actual usage first. Unused code gets removed (YAGNI), not polished.

   Done when: every item has a verdict with evidence.
4. **Respond** per verdict:
   - **Implement** → state the fix: "Fixed — [what changed, where]." The fix itself is the acknowledgment — no praise, no gratitude, no "you're absolutely right".
   - **Push back** → technical reasoning and specific questions, referencing working code or tests. If the suggestion conflicts with your human partner's prior decisions, bring it to them before acting.
   - **Can't verify** → say so: "Can't verify without [X]. Investigate, ask, or proceed?"
5. **Implement** in order: blocking issues (breakage, security), then simple fixes, then complex ones. One item at a time. Done when: every implement-verdict is coded, individually tested, and checked for regressions.

## Source calibration

- **Your human partner** — trusted: confirm scope, then act.
- **External reviewers** — skeptical: full verification; they may lack context. You and the reviewer both report to the same person, so a feature nobody needs stays unbuilt even when the reviewer asks for it.

## Correcting your own pushback

If verification proves you wrong, state it factually and move on: "You were right — checked [X], it does [Y]. Fixing." The correction needs no apology or defence.

## GitHub inline comments

Reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as a top-level PR comment.
