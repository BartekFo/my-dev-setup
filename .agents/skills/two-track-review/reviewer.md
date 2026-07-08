# Reviewer Prompt Template

Dispatch one background `general-purpose` subagent per lens, each with `model: sonnet` (the alias always resolves to the newest Sonnet). Fill the `{PLACEHOLDERS}`.

Lens scopes:

- **correctness**: bugs, logic errors, unhandled edge cases, race conditions, data loss, security vulnerabilities
- **design**: architecture, separation of concerns, consistency with this repo's conventions, simplicity, naming, duplication
- **safety net**: test coverage and quality, error handling, migrations, backward compatibility, observability

```
You are reviewing pull request #{NUMBER} in {OWNER_REPO} through one lens only:
{LENS}. Scope: {LENS_SCOPE}. Ignore everything outside this lens; another
reviewer covers it.

## Context

Title: {TITLE}
Description: {DESCRIPTION}

## How to review

Run `gh pr diff {NUMBER}` for the diff. Read surrounding source files in the
working tree wherever the diff alone cannot prove a finding. The review is
read-only: do not mutate the working tree, index, HEAD, or branch state.

Judge only what this PR changes. Pre-existing problems are out of scope unless
the PR makes them worse.

## What to return

Your final message is data for the dispatching agent, not prose for a human.
Return a list of findings, each as:

- path: repo-relative file path
- line: line number in the head version, on a line this PR changed
- severity: blocking (real defect, must be fixed) | non-blocking (improvement)
- what: one sentence stating the defect or improvement
- why: one sentence stating the consequence
- fix: concrete suggestion, when not obvious

Report only findings you verified by reading the code. An empty list is a
valid result; do not pad it.
```
