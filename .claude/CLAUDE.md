# Workflow Orchestration

## Code Styles

- Dont use inline style={{}} create css modules for components that need them
- Always check component on frontend before using components directly from library like mantine
- Never use nester nested ternary operator

## Commenting style

- Never add comments saying "What". Only add comments explaining "Why" but ONLY if they are needed.

## Code search

When searching for TypeScript functions, classes, or types, prefer mcp__serena__find_symbol over Grep. Use Grep only for string literals, comments, or non-code patterns.
ALWAYS check if there are existing backend services or utility functions that already handle similar filtering before writing new logic.
ALWAYS USE `rg`(ripgrep) instead of grep
ALWAYS USE fd intead of find Always use `fd` instead of `find` when you search for file!

## Git & PR Workflow

- When creating PRs, always ensure the branch is pushed to the remote before attempting to create the PR. Use `git push -u origin <branch>` first.

## Plan Mode Default

Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)

If something goes sideways, STOP and re-plan immediately – don't keep pushing

Use plan mode for verification steps, not just building

Write detailed specs upfront to reduce ambiguity

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

Zero context switching required from the user

Go fix failing CI tests without being told how

## Core Principles

Simplicity First: Make every change as simple as possible. Impact minimal code.

No Laziness: Find root causes. No temporary fixes. Senior developer standards.

## Minimal Impact: Changes should only touch what's necessary. Avoid introducing bugs
