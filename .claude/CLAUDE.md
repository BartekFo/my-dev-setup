# Workflow Orchestration

  → When the user corrects you, stop and re-read their message. Quote back what they asked for and confirm before proceeding.
  → Read the full file before editing. Plan all changes, then make ONE complete edit. If you've edited a file 3+ times, stop and re-read the user's requirements.
  → When stuck, summarize what you've tried and ask the user for guidance instead of retrying the same approach.
  → Every few turns, re-read the original request to make sure you haven't drifted from the goal.
  → Act sooner. Don't read more than 3-5 files before making a change. Get a basic understanding, make the change, then iterate.
  → Re-read the user's last message before responding. Follow through on every instruction completely.
  → After 2 consecutive tool failures, stop and change your approach entirely. Explain what failed and try a different strategy.
  → Double-check your output before presenting it. Verify that your changes actually address what the user asked for.

## Code Styles

- Always check component on frontend before using components directly from UI Library
- Never use nester nested ternary operator

## Commenting style

- Never add comments saying "What". Only add comments explaining "Why" but ONLY if they are needed.

## Code search

ALWAYS check if there are existing backend services or utility functions that already handle similar filtering before writing new logic.
ALWAYS USE `rg`(ripgrep) instead of grep
ALWAYS USE `fd` instead of `find` when you search for file!

## Self-Improvement Loop

After ANY correction from the user create proposition for updating workflow Orchestration

Write rules for yourself that prevent the same mistake

Ruthlessly iterate on these lessons until mistake rate drops

Review lessons at session start for relevant project

## Demand Elegance (Balanced)

For non-trivial changes: pause and ask "is there a more elegant way?"

If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"

Skip this for simple, obvious fixes – don't over-engineer

Challenge your own work before presenting it

## Autonomous Bug Fixing

When given a bug report: just fix it. Don't ask for hand-holding

Point at logs, errors, failing tests – then resolve them

## Core Principles

Simplicity First: Make every change as simple as possible. Impact minimal code.

No Laziness: Find root causes. No temporary fixes. Senior developer standards.

## Minimal Impact: Changes should only touch what's necessary. Avoid introducing bugs
