---
name: test-gate
description: Value gate for tests. Use when writing, changing, or reviewing a test, or when deciding whether a change needs one.
---

# Test gate

A test earns its maintenance cost only when it protects observable behavior, an invariant, or a contract, and goes red on a credible regression. Repository testing docs (`AGENTS.md`, `CLAUDE.md`, `docs/testing*`) win where they are stricter.

## Gate

Answer all four before you add or keep a test. A missing answer means no test yet.

1. **Behavior** — what observable outcome, invariant, or contract does it protect?
2. **Regression** — what credible code change turns it red?
3. **Owner** — why does no existing test catch that change? Each contract has one owner test at the strongest boundary. Extend a table-driven case before you write a near-duplicate.
4. **Seam** — does it need an export, flag, or hook that no production caller uses? Then move the test to the real boundary.

A test that goes red under a behavior-preserving refactor asserts implementation. Rewrite it at the owner boundary.

A regression test must go red on the pre-fix code for the intended reason. Write it at the owner boundary once, not at every layer the bug crosses.

## Tautology

A **tautological** test passes by construction: the expected value and the actual value come from the same source. It stays green when the behavior breaks. Forms:

- expected value computed by the function under test, or by a copy of its logic;
- the mock returns X, the test asserts X;
- the test passes prop X, the test asserts X is rendered;
- the test asserts a mock was called with a literal copied from the source;
- the fixture supplies the ordering, receipt, or state the code should produce.

Compute expected values by hand, as literals, from the domain rule.

## Frontend: thin UI layer

Put logic in pure functions and hooks, and test it there. Components stay thin, and so do their tests.

A component test earns its place only when one of these holds:

- a user interaction produces an observable outcome that a unit test cannot reach: a callback with a domain payload, navigation, a visible state change;
- a domain rule (role, stage, permission) decides what renders and no pure function owns that rule yet. The better fix is to extract the rule and unit-test it.

Use copy and accessible names as **locators** to reach the interaction (`getByRole("button", { name: /save/i })`), not as the assertion goal.

These belong to the design, not to tests: styles, classes, colors, layout sizes, static copy, icons, which props a parent forwards to a child, that a component renders at all, snapshots, and library behavior (Mantine opens a modal, a table sorts).

Render real children and the design system. Mock at the network boundary or inject a seam. A test that mocks the component's own children asserts wiring, not behavior.

## Junk patterns

Shared checklist. The gate rejects a new test that matches one. An audit hunts existing tests that match one.

- no assertion; self-comparison;
- tautology (any form above);
- static copy, style, class, or color assertions on rendered output;
- render smoke: "renders without crashing", "container is not empty";
- snapshots of component output;
- props-capture: a mocked child records props, the test asserts them;
- call-shape: assertions on args to a mocked internal module, with no user-visible outcome;
- exact source, import, or string greps;
- duplicate tests of one contract; provider-local replays of shared helpers;
- tests that keep test-only exports, flags, or wrappers alive; production code whose only callers are tests;
- negative controls that pass for an unrelated reason;
- names that promise more than the assertions check.

## Retention bar

Keep a test when it independently guards a public API, protocol, config, migration, storage, security, permission, money or date math, or architecture contract. Also keep:

- call ordering when the order is observable;
- a regression with a credible failure mode;
- a source check when it is the cheapest independent guard of a user-facing key, byte, or path.

A slow or static test is not junk by itself. A kept test that fails on the baseline is a possible product bug: reproduce it and fix the owner.
