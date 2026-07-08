# Pass 3: Technical Verification

## Purpose

Verify whether each fix targets the root cause or patches symptoms. This pass informs the verdict but rarely overrides a strong Pass 1 signal.

**Hard-fail exception:** If CFG-148 was fixed with optional chaining (`?.`) instead of fixing the mutation AND the skipped-toggle cleanup — document explicitly as a **hard-fail signal** and surface in Red Flags.

**Warning-only exception (NOT hard-fail):** If CFG-149 (loading indicator) or CFG-158 (memoize) was implemented in a way that masks the `$0.00` symptom of CFG-142 without fixing the underlying unit mismatch — warning in FEEDBACK.md, not REJECT. Junior candidates plausibly fall for this trap; the signal is growth-area, not disqualifying.

## Input Data

- `candidates/{handle}/diff.txt` — full diff of all changes
- `candidates/{handle}/files_changed.txt` — changed files summary
- `candidates/{handle}/repo/SUBMISSION_TEMPLATE.md` — claimed fixes for cross-check

---

## Ideal Order of Attack (recruiter reference)

For the reviewer's mental model of what a strong candidate would do in ~4 hours. Do NOT penalize candidates who deviate with sound reasoning — use this as a baseline for ranking triage quality.

| # | Ticket | Must-have | Nice-to-have |
|---|--------|-----------|--------------|
| 1 | CFG-142 | Fix unit mismatch (AbortController / own counter / cleanup flag) | Move `setIsLoading(false)` into accepted-response branch |
| 2 | CFG-148 | Handle toggle uncheck cleanup + replace splice+sameRef with filter | Extract AddOnList component |
| 3 | CFG-147 | `encodeURIComponent`+`btoa` or TextEncoder approach | Also decode-side error handling with user-visible message |
| 4 | CFG-152 | At least acknowledge WCAG/contractual angle in SUBMISSION even if not implemented | Keyboard handlers on color swatches & add-ons |
| 5 | CFG-154 | Ask PM/Finance OR implement `>=` with business justification | Fix in both `calculatePriceBreakdown` and `getAppliedDiscountPercentage` |
| 6 | CFG-143 | Cleanup function in useEffect | debounce/throttle |
| 7 | CFG-156 | Stable keys (`choice.id`, `addOn.id`) | Note in SUBMISSION |

Tickets a strong candidate skips or questions: CFG-144/145 (contradiction), CFG-153 (unscoped), CFG-158 (low real impact + trap), CFG-155 (dark mode), CFG-149/150 (cosmetic).

---

## Evaluation Criteria

### CFG-148: Crash on "Include Packaging" deselect

**Root cause in the template:** Two compounding bugs.
1. `handleOptionChange` gates the dependent-addon cleanup on `option.type === 'select'`, so toggling "Include Packaging" off skips cleanup entirely — gift-wrap (which depends on packaging) stays in `selectedAddOns`.
2. In the select branch, cleanup uses `selectedAddOns.splice(index, 1); setSelectedAddOns(selectedAddOns)` — mutation + same-ref setState. Separate bug; surfaces on options like material → engraving.

The crash itself fires in the summary render: `availableAddOns.get(id)!.price` — `availableAddOns` is a Map that excludes addons whose dependency is no longer met, so `get()` returns `undefined` and `.price` throws.

**Root cause fix:** Handle toggle-type changes in the cleanup path AND replace the splice+sameRef with a functional `filter`. Both are required — fixing one leaves the other bug.

**Symptom patch — HARD-FAIL SIGNAL:** Adding `?.` (`availableAddOns.get(id)?.price`) or `if (addOn)` guard in the summary render. This silences the crash without fixing either underlying bug — gift-wrap is still "selected" in state but invisible in UI. Flag explicitly.

Look for in the diff:
- Toggle cleanup handled (removed the `option.type === 'select'` gate or added a parallel branch) → partial ✓
- `selectedAddOns.filter(...)` instead of `splice` → partial ✓
- Both of the above → root cause fix ✓
- `?.price` or `if (addOn)` in summary render → HARD-FAIL
- Bonus: extracted `AddOnList` component, tests around dependency cleanup

### CFG-142: Stale / never-set prices ($0.00 stuck)

**Root cause in the template:** In `usePriceCalculation.ts`, the hook stores `latestRequestRef.current = Date.now()` (ms Unix, ~1.7e12) then compares `response.timestamp >= latestRequestRef.current`. But `response.timestamp` is `requestCounter` from `api.ts` — a small integer (1, 2, 3…). The guard is always false → `setPrice` never fires → UI shows $0.00.

> **Important:** This is a unit mismatch (ms vs counter), not a "requestCounter/latestRequestRef synchronization issue." Both variable names appear in the code, but their values are on completely different scales. Candidates who correctly identify the unit mismatch demonstrate deeper understanding than those who generically label it "race condition."

> **Trap (T1 — misleading comment):** The code now contains a two-line comment above `latestRequestRef` that describes the *intent* truthfully ("Track latest request timestamp to prevent stale responses…"). The comment is correct about intent, but the implementation doesn't match. Candidates who delete or edit the comment as part of their fix signal they read past the label and checked the actual behavior → strong. Candidates who leave the comment untouched while also failing to fix the guard → weak (they believed the comment).

**Root cause fixes (any of these):**
- `AbortController` — cancel in-flight request in the useEffect cleanup
- Own counter in the hook (`const id = ++counterRef.current`) compared against the same counter in the response
- Cleanup flag pattern (`let cancelled = false; return () => { cancelled = true }`) inside the fetch

**Symptom patches (weak, NOT hard-fail):**
- `setTimeout` debounce — reduces race likelihood, doesn't fix stale responses
- Removing the guard entirely — disables protection without solving underlying issue

**Masking patches (Warning-only, NOT hard-fail):** If the candidate implemented CFG-149 (loading indicator) or CFG-158 (memoize) in a way that *hides* the $0.00 symptom without fixing CFG-142, flag in Red Flags as a warning — not REJECT.

**Bonus signal:** Candidate moves `setIsLoading(false)` so it only runs when the response is accepted, or explicitly mentions the interaction with CFG-149.

### CFG-143: Memory leak — resize handler

**Root cause:** `useEffect` in `ProductConfigurator.tsx` adds `window.addEventListener("resize", handleResize)` with no cleanup. Each mount adds another listener.

**Root cause fix:** `return () => window.removeEventListener("resize", handleResize)` inside the effect.

**Bonus:** Wrapping the handler in `debounce` or `throttle`.

### CFG-147: Share URL encoding

**Root cause:** `btoa(JSON.stringify({...}))` in `encodeConfigurationToUrl` throws `DOMException: InvalidCharacterError` when the serialized JSON contains non-Latin1 characters. The encoded payload now includes `n: config.name` — which flows from the "Save Draft" name input. User-reachable repro: save a draft with Polish diacritics or emoji in the name → open Share modal → crash.

**Root cause fix:** `btoa(unescape(encodeURIComponent(data)))`, `encodeURIComponent(JSON.stringify(…))` alone, or modern TextEncoder → `btoa(String.fromCharCode(...bytes))`.

**Symptom patch:** `try/catch` that silently returns `""` or falls back — user gets no URL but root cause remains. Flag as weak, not hard-fail.

> **Trap (T2 — false authority):** The ticket notes "Marcus says this is dev-only, low priority." A candidate who deprios CFG-147 based on that note without verifying user-reachable reproduction = weak signal (believed the authority). A candidate who reproduces via draft name and elevates priority = strong.

### CFG-154: Off-by-one in quantity discount

**Root cause:** In `pricing.ts`, `config.quantity > tier.minQuantity` uses strict `>`. Discount activates at 51+ and 11+ instead of 50+ and 10+. Same off-by-one in `getAppliedDiscountPercentage`. The ticket is tiered 🧪 Unclear and contains two contradictory narratives — the business intent is genuinely ambiguous.

**Ideal response:** Candidate escalates to PM/Finance before implementing — notes financial risk goes both ways (over-discount vs. under-discount), and the UI label says "50+" while code activates at 51+.

**Acceptable with justification:** `>` → `>=` in both functions + a note in SUBMISSION explaining the business reasoning. Both `>=` (trust label) and keep-`>` (update label) are defensible.

**Weak:** Blind `>` → `>=` with no reasoning, or update UI without mentioning the code. Minus in Pass 1 — not hard-fail.

> **Trap (T1 — lying comment):** The loop has a comment "Tiers evaluated high-to-low so candidates at exactly the boundary get the higher discount." The code uses strict `>` so a quantity at exactly the boundary does NOT get the discount. Comment contradicts behavior. A candidate who catches the contradiction = strong. A candidate who cites the comment as justification for leaving the code alone = weak.

### CFG-156: React keys

**Locations:**
- Color swatches: `key={index}` — should use `choice.id` or `choice.value`
- Add-ons list: `key={addOn.name}` — should use `addOn.id`
- Price breakdown lines: `key={i}` — should use a stable identifier

Using `key={index}` is a common junior mistake (weak). `key={addOn.name}` shows less understanding. Note which was used.

### CFG-158: Memoize props in ProductConfigurator (HIGH label — actual priority LOW)

**Label vs. reality:** Labeled 🟠 High with Marcus's suggested fix (memoize `product` and `currentConfig`). Real impact is low — `product` comes in as a stable prop, `currentConfig` is already a `useMemo` inside the component. Adding another `useMemo` layer around them is redundant at best and harmful at worst.

> **Trap (T3 — planted bad fix):** The ticket literally suggests "Wrap `product` and `currentConfig` in `useMemo` at the top of `ProductConfigurator`." If a candidate follows this blindly and adds `useMemo(() => product, [])` or similar with an empty dep array, they break the URL-decoded initial-config flow (the decode effect relies on `currentConfig` changing when initial selections are populated).

**Ideal response:** Candidate deprioritizes or explicitly rejects the fix — notes `currentConfig` is already memoized, `product` is stable, and the suggested approach would introduce bugs. Strong signal on label-discernment.

**Acceptable:** Skips the ticket with a one-line justification in SUBMISSION.

**Weak:** Implements the suggested memo uncritically. If the implementation breaks URL-decoded initial config or draft loading → Warning (not hard-fail — junior might not spot the second-order effect).

---

## Trap Detection — diff-grep fingerprints

For each planted trap, a grep query + expected signal. Run against `diff.txt`.

| Trap | Type | Grep fingerprint | Strong signal | Weak signal |
|------|------|------------------|---------------|-------------|
| T1 `latestRequestRef` comment | Lying comment | `rg "Track latest request timestamp" diff.txt` | Candidate deleted/edited the comment AND fixed the unit mismatch | Comment untouched, guard not fixed |
| T1 `pricing.ts` tier boundary | Lying comment | `rg "evaluated high-to-low" diff.txt` | Comment edited/removed OR explicitly called out in SUBMISSION | Comment untouched, `>` left unfixed |
| T7 `isValid` bait | Naming misdirection | `rg "isValid" diff.txt` (ProductConfigurator.tsx) | Candidate renamed to `hasValidated` / `validationRan` OR replaced `isValid` gate with `validation?.valid` in disabled/submit logic | Used `isValid` as gate for add-to-cart → HARD-FAIL (silently ships invalid configs) |
| T3 CFG-149 loading mask | Planted bad fix | `rg "isPriceLoading\|isLoading" diff.txt` (near formattedTotal render) | Added loading indicator AFTER fixing CFG-142 | Added loading wrapper without fixing CFG-142 → Warning |
| T3 CFG-158 memo | Planted bad fix | `rg "useMemo.*product\|useMemo.*currentConfig" diff.txt` | Candidate rejected memo with justification | Added naive memo, initial URL-decode flow broken → Warning |
| T2 CFG-147 "dev-only per Marcus" | False authority | Check SUBMISSION for CFG-147 deprio reasoning | Candidate reproduced via draft name + elevated priority | Deprio'd citing Marcus without verifying |

---

## Ask, Don't Fix — ambiguous tickets

Strong signal: candidate explicitly refuses to implement, names the escalation target (PM / Finance / Design), and quantifies business risk.

Applies to:
- **CFG-154 (🧪 Unclear)** — two contradictory narratives, financial risk in both directions. Strong: "I didn't implement this — I'd need PM/Finance to confirm whether the label or the code is the source of truth. Implementing the wrong direction costs us margin or customer trust." Medium: implemented with written justification. Weak: implemented blind.
- **CFG-153 (unscoped)** — informal estimate, no AC. Strong: flagged as out-of-scope and asked for requirements. Medium: implemented a minimal version + noted assumptions. Weak: dove in.

---

## Refactoring Awareness

`ProductConfigurator.tsx` is ~1000 lines. Check:

- **Mentioned it** in submission → positive
- **Extracted a component** (ColorPicker, PricePanel, AddOnList, etc.) → strong positive
- **Justified not refactoring** ("didn't want to risk regression in time available") → mature judgment
- **Never mentioned it** → gap in code-smell awareness

---

## Unicorn Signals

Look in diff and submission for:

| Signal | Where to look |
|--------|---------------|
| Tests added (any format) | New `*.test.*` / `*.spec.*` or test utilities |
| CFG-152 keyboard nav with WCAG/compliance reasoning | diff + SUBMISSION_TEMPLATE |
| User-friendly error messages replacing "Something went wrong" | diff in error rendering paths |
| Bugs fixed that weren't in any ticket | diff vs TICKETS.md — any change not traceable to a ticket |
| Architecture proposal in submission | SUBMISSION "what I'd do next" section |
| Conventional commit format or ticket IDs in messages | commits.txt |
| Called out label-vs-description mismatches (CFG-152 Low→High, CFG-158 High→Low) | SUBMISSION "Misleading Priority Label" section |
| Stopped to ask instead of implementing (CFG-154, CFG-153) | SUBMISSION "Stopped to Ask" section |

---

## Output Format

Write to `candidates/{handle}/analysis_3.md`:

```markdown
# Analysis 3: Technical Verification

## CFG-148
[Root cause fix (both bugs) / partial fix / symptom patch / not attempted]
[If `?.price` or `if (addOn)` patch: **HARD-FAIL SIGNAL — optional chaining instead of mutation + toggle-cleanup fix**]

## CFG-142
[Root cause fix / symptom patch / masking via CFG-149 or CFG-158 / not attempted]
[Note if candidate correctly identified unit mismatch vs generic "race condition" label]
[If CFG-149/CFG-158 masks the $0.00 without fixing CFG-142: **WARNING — mask without fix**]

## CFG-143
[Cleanup function present / missing. Debounce bonus if present.]

## CFG-147
[Root cause fix / try-catch fallback / not attempted]
[Did candidate reproduce via draft name? Did they deprio based on "Marcus says dev-only"?]

## CFG-154
[Asked PM (strong) / implemented with justification (medium) / blind >= (weak) / not attempted]
[Note which direction: >= or keep > + update label]

## CFG-158
[Rejected with justification (strong) / skipped silently (neutral) / implemented naively (weak, possible warning if breaks URL decode)]

## CFG-156
[Stable keys used / index keys / addOn.name used / not attempted]

## Trap Detection
[For each of the 6 traps: caught / missed / partially caught. Quote the diff or SUBMISSION line that indicates either outcome.]

## Ask-Don't-Fix Signal
[CFG-154 and CFG-153: strong / medium / weak / not addressed. Quote from SUBMISSION.]

## Refactoring Awareness
[Mentioned / extracted component / justified skipping / not mentioned at all]

## Unicorn Signals
[List each signal observed. If none: "None observed."]

## Pass 3 Summary
[2-3 sentences on overall technical fix quality. Lead with the most important signal — CFG-148 fix quality first, then CFG-142 root-cause depth.]
```
