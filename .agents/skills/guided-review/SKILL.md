---
name: guided-review
description: Guided PR review. Builds a local reading guide (overview, before/after flow diagram, chapters in reading order) and opens it in the browser.
disable-model-invocation: true
---

# Guided Review

Turn a pull request into a **guide**: an overview, a before/after flow diagram, and **chapters** that group the diff by idea in reading order. The guide explains the PR; it never judges it. The guide stays local and never reaches the PR.

Argument: PR number or URL. Without it, use the PR of the current branch.

`render.py` sits next to this file. `{SKILL_DIR}` is this skill's base directory.

## Step 1: Load the PR

Work in `DIR=/tmp/guided-review/<owner>-<repo>-<number>`:

```bash
mkdir -p $DIR
gh pr view <pr> --json number,title,url,author,headRefOid,additions,deletions > $DIR/pr.json
gh pr diff <pr> > $DIR/diff.patch
```

Done when: both files exist and `python3 {SKILL_DIR}/render.py hunks $DIR` lists every changed file.

## Step 2: Write the guide

Dispatch one foreground subagent with the template in [guide.md](guide.md). It writes `$DIR/guide.json`.

Done when: `python3 {SKILL_DIR}/render.py check $DIR` exits 0 when you run it yourself.

## Step 3: Open it

```bash
python3 {SKILL_DIR}/render.py render $DIR && open $DIR/guide.html
```

The page keeps per-chapter and per-file "Reviewed" checkboxes in the browser, keyed to the head SHA. Report the overview sentence, the numbered chapter titles, and the file path.

Done when: the page is open in the browser.

## Step 4: Read along

The user reads chapter by chapter and asks questions; answer from the code with `path:line`. When the user wants to comment, point them to `/two-track-review` in this conversation: it groups its draft by these chapters.
