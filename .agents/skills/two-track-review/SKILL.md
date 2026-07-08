---
name: two-track-review
description: Two-track PR review. Background subagents deep-review while you review by hand; findings become a Conventional Comments draft you curate, then post as inline PR comments.
disable-model-invocation: true
---

# Two-Track Review

Review a pull request on two tracks: subagents review in depth while the human reviews by hand. Both tracks merge into one **draft** of Conventional Comments. Every comment is **anchored** to a line in the diff. Nothing reaches the PR before explicit **sign-off**. This skill reports and posts comments; it never edits the PR's code.

Argument: PR number or URL. Without it, use the PR of the current branch.

## Step 1: Load the PR

Collect with `gh`:

- owner/repo, PR number, title, description (`gh pr view --json ...`)
- head commit SHA (`headRefOid`)
- full diff (`gh pr diff`)

Done when: head SHA and diff are in hand.

## Step 2: Dispatch reviewers, get out of the way

Dispatch three background subagents, one per lens, filling the template in [reviewer.md](reviewer.md):

- **correctness**: bugs, logic errors, edge cases, races, data loss, security
- **design**: architecture, repo conventions, simplicity, naming, duplication
- **safety net**: tests, error handling, migrations, backward compatibility

Each lens is blind to the others. Then tell the user the reviewers are running and that this is the window for their manual track. End the turn; background completion resumes you. Do not poll.

Done when: all three reviewers reported.

## Step 3: Draft

Merge both tracks' findings into one numbered draft:

- Dedupe overlapping findings; keep the sharper wording.
- Convert each finding to a Conventional Comment (reference below). Map severity honestly: a real defect is `issue (blocking)`, an improvement is `suggestion (non-blocking)`, never inflate.
- Anchor each comment to `path:line` where the line is part of the diff (head side). A finding on unchanged code goes to the review body instead; never invent an anchor.

Present the full draft in chat, each entry as:

```
N. path:line
   label (decoration): subject

   discussion
```

Done when: every entry has a verified anchor or is explicitly marked "review body".

## Step 4: Curate

The user folds in their manual-track findings and edits the draft: add, drop, reword, relabel, change decorations. After every change re-present the full draft. Dropped entries leave gaps; numbers never shift.

Sign-off is an explicit instruction to post ("post it", "wysyłaj"). Agreement-sounding chatter is not sign-off. Never post without it.

Done when: the user gives sign-off.

## Step 5: Post

Submit one review in a single call:

- event: `REQUEST_CHANGES` if any comment carries `(blocking)`, else `COMMENT`. `APPROVE` only if the user said so during sign-off.
- body: one-line summary plus any "review body" findings. The summary describes the findings only; never mention the review process, this skill, its name ("two-track"), subagents, or any other internal tooling anywhere in the posted review.
- comments: the anchored entries, verbatim from the draft

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --input review.json
```

```json
{
  "commit_id": "<head SHA>",
  "event": "COMMENT",
  "body": "...",
  "comments": [
    { "path": "src/file.ts", "line": 42, "side": "RIGHT", "body": "suggestion: ..." }
  ]
}
```

For a multi-line anchor add `start_line` and `start_side`. If the API rejects an anchor (422), re-check it against the diff and retry once; if it still fails, move that comment into the body and tell the user.

Done when: the review is visible on the PR and its URL is reported.

## Conventional Comments

Format: `<label> (<decorations>): <subject>`, blank line, discussion.

| label | use for |
|---|---|
| praise | something genuinely well done |
| issue | a concrete problem the code introduces |
| suggestion | a proposed improvement with a clear why |
| question | a real question or potential concern |
| nitpick | trivial preference, always non-blocking |
| todo | small, necessary, mechanical change |
| thought | non-actionable idea worth sharing |
| chore | process task required before acceptance |

Decorations: `(blocking)` must be resolved before acceptance, `(non-blocking)` should not block acceptance, `(if-minor)` resolve only if the fix is trivial. An undecorated `issue` reads as blocking to most teams, so decorate deliberately.
