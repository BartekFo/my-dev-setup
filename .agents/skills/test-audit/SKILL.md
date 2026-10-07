---
name: test-audit
description: Audit a repo's tests with a deterministic scan and mutation proof, delete low-value tests, and open one PR per batch.
disable-model-invocation: true
argument-hint: "[package] [path] [--apply]"
---

# Test audit

Sweep one package's tests, prove which ones protect nothing, delete them in one coherent batch, and open a PR. The value bar is `../test-gate/SKILL.md`: read it first, completely. Optimize for confidence, not deletion count.

`$S` below is this skill's `scripts/` directory. All scripts run from anywhere inside the target repo, need only Node 22+ and the repo's own `typescript`, and keep state in `<repo>/.test-audit/` (git-excluded locally).

Modes: without `--apply`, stop after step 5 and report. With `--apply`, run every step and open the PR.

## Steps

1. **Setup.** Read the root and scoped `AGENTS.md` / `CLAUDE.md` and the repo's testing docs. Run `node $S/init.mjs`. On a first run, show `.test-audit/config.json` to the user and fix `runTests`, `checks`, `branchPattern`, `uiLibraries`, `designSystem`, and `scopeDepth` (path segments under a scope root that make one batch) with them. Start from a clean tree on the updated base branch. Done when the config is confirmed and `runTests` for the package passes.

2. **Scan.** Run `node $S/scan.mjs --package <name> [--path <dir>]`, then `node $S/seams.mjs --package <name>` (skip if knip is absent), then `node $S/batch.mjs`. Done when `.test-audit/batches/index.json` exists and you have shown the user the summary and the batch list.

3. **Pick a batch.** Take the batch the user names, else the largest one. One batch = one PR. Done when one worksheet `.test-audit/batches/<id>.md` is chosen.

4. **Prove.** Run every `mutate.mjs` command listed in the worksheet, **one at a time**: each run edits the owner file temporarily and restores it. Never edit files while it runs. When the owner delegates logic to a hook or helper, also mutate that file with `--tests` set to the same test files. Done when every owner in the batch has `.test-audit/mutations/<owner>.json`.

5. **Triage.** For every candidate in the worksheet, read the complete test, its owner, the owner's callers, and the overlapping tests. Use `git log -L` or `git log --follow` for history. Fill every field of the candidate's table. A missing field means the verdict is `keep`. Pick the verdict:

   | verdict | when |
   | --- | --- |
   | `delete` | matches a junk pattern, and mutation says `no-kill` / `change-detector`, or `redundant` with a safe drop set (step 6) |
   | `extract-logic` | the test is the unique killer of a logic mutant, but reaches the rule through the UI. Move the rule into a pure function or hook, unit-test it there, delete the UI test |
   | `rewrite` | unique killer, but coupled to implementation (props-capture, call-shape). Rewrite it at the owner boundary |
   | `keep` | meets the retention bar. Record why: it is a false positive to report |

   Also scan the worksheet's "review only" lines and promote a test when you see a junk pattern. Done when no table in the worksheet has an empty cell. Without `--apply`, report now (see Handoff) and stop.

6. **Verify the drop set.** Per owner, write the `delete` and `extract-logic` test keys (exactly as `mutate.mjs` prints them) to a JSON array and run `node $S/mutate.mjs --package <name> --owner <owner> --drop <file.json>`. `UNSAFE` means a dropped test is the sole killer of a logic mutant: change that test's verdict and rerun. Done when every owner prints `safe`.

7. **Edit.** Apply the verdicts. Delete tests, then the mocks, fixtures, helpers, and imports they alone used, then empty test files, then test-only exports from `seams.json`. For `extract-logic`, do the extraction when it fits in the batch; else list it as a follow-up and keep the test. Add no replacement test that restates the implementation. Done when every verdict is applied or listed as a follow-up.

8. **Validate.** Run `runTests` on every touched test file, run the package `checks` from the package root, run `git diff --check`, and rerun `mutate.mjs` for each owner whose tests changed. The logic-kill count must not drop. Rerun `scan.mjs` and record the before/after counts. Run `git diff --numstat` and split production LOC from test LOC. A check that also fails on the base branch is pre-existing: report it and leave it out of this PR. Done when everything else is green and the kill counts match.

9. **PR.** Create the branch from `branchPattern` (ask for a ticket when it has `{ticket}`). Commit with a conventional message, push, and open the PR with `gh pr create --base <baseBranch>`, filling `prTemplate`. The body carries the Handoff content. Done when `gh` returns the PR URL.

## Detectors

`scan.mjs` flags; the weight is in brackets. A score at or above `minScore` makes a candidate. Flags are leads, not verdicts: the mutation proof and your reading decide.

| flag | meaning |
| --- | --- |
| `no-assertion` [3] | no `expect`/`assert` in the body or called helpers |
| `self-compare` [3] | `expect(x).toBe(x)` |
| `sut-computes-expected` [3] | the expected value calls the function under test (relational `f(a) !== f(b)` is skipped) |
| `render-smoke` [3] | one assertion that the container exists or is not empty |
| `static-copy` [3] | render, no interaction, only presence checks on copy that the owner renders unconditionally |
| `props-echo` [3] | render, no interaction, asserts text the test file itself supplied |
| `style-assertion` [3] | `toHaveStyle`, `toHaveClass`, `className`, `style`, `data-variant` on rendered output |
| `props-capture` [2] | asserts props recorded by a mocked child component |
| `snapshot` [2] | snapshot matcher |
| `source-grep` [2] | reads source text |
| `duplicate-body` [2] | same normalized body as another test |
| `skipped` [2] | `.skip` / `.todo` |
| `call-echo` [2] | asserts a mock was called with a literal copied from source |
| `conditional-render` [1] | render, no interaction, presence checks on a branch. Often a domain rule to extract |
| `call-shape` [1] | asserts args recorded by a mocked internal module |
| `mock-call-only` [1] | render, then only mock-call assertions |

`mutate.mjs` mutates only the owner file in three categories: `logic` (operators, conditions, booleans, compared literals, removed calls), `copy` (JSX text, label-like attributes), and `style` (`className`, `style`, Mantine style props). Per test, the verdicts are:

- `no-kill`: catches nothing in the owner;
- `change-detector`: catches only copy or style edits;
- `redundant`: every logic mutant it kills, another test also kills;
- `unique`: sole killer of at least one logic mutant.

`minimal cover` is the smallest test set that keeps every logic kill. Surviving logic mutants are coverage gaps: report them, and do not fill them in this PR.

## Handoff

Report in chat, and in the PR body:

- removed tests by detector and verdict, with the before/after scan counts;
- logic-kill counts per owner, before and after (they must match);
- production simplifications (seams, mocks, helpers removed);
- kept false positives and why they stay;
- `extract-logic` and `rewrite` follow-ups, and surviving logic mutants;
- commands run, and production versus test LOC;
- PR URL, then the next batch from `index.json`.
