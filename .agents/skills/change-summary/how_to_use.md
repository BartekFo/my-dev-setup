# 🧠 Change Summary Skill — How to Use

This guide explains how to use the **Change Summary Skill**, which converts technical changes into clear, business-oriented updates and posts them to Linear, Jira, or outputs them for copy-paste.

---

## 🎯 Purpose

The skill helps you:

* Translate code changes into **stakeholder-ready summaries**
* Keep issue trackers **well-documented and non-technical**
* Maintain consistent update quality across the team
* Quickly generate copy-pasteable release notes or client updates

---

## 🌐 Supported Platforms

| Platform | How to trigger |
|----------|---------------|
| **Linear** | Provide or auto-detect a Linear issue ID (e.g. `ABC-123`) |
| **Jira** | Provide or auto-detect a Jira issue key (e.g. `PROJ-456`) |
| **Output only** | Say "just output it here" or leave the destination open |

The skill infers the destination from branch name, commit messages, or available MCP tools. If ambiguous, it will ask.

---

## 🚀 Basic Usage

### 1. Trigger the skill

Provide a diff, commit, or description of changes:

```
summarize this diff
```

or

```
summarize changes for this branch
```

---

### 2. Answer the audience question

Before generating, the skill will ask:

```
Who is the intended reader of this summary?
(e.g. CEO, PM, client, QA lead — and optionally their background or industry)
```

Examples of useful answers:
- `PM at a SaaS company, non-technical`
- `CTO, familiar with engineering but not this codebase`
- `external client, no technical background`
- `default` — uses a generic non-technical PM persona

This calibrates tone, vocabulary, and level of detail in the output.

---

### 3. Confirm or provide destination

The skill will try to detect where to post (Linear, Jira, or output only). If it can't determine it, it will ask:

```
Where should I post this summary?
(e.g. Linear ABC-123 / Jira PROJ-456 / just output it here)
```

---

### 4. Review Generated Summary

The skill generates a structured Markdown summary inside a fenced block (ready to copy):

````markdown
```markdown
## 📝 Summary
...

## 🚀 User Impact
...

## 🔧 Improvements
...

## 📌 Notes (optional)
...
```
````

This content is:

* Written in **English**, calibrated to the stated audience
* Focused on **business value and outcomes**
* Free from technical jargon (see jargon blocklist in SKILL.md)
* Written to sound human — varied sentence length, active verbs, no AI-isms

---

### 5. Confirm Before Sending

You will be asked:

```
Do you want me to post this to Linear issue ABC-123?
```

Available actions:

* `yes` → posts to the resolved destination
* `edit: ...` → modifies the summary and regenerates
* `copy` → summary is already in the fenced block above, no posting needed
* `cancel` → aborts entirely

⚠️ Nothing is sent automatically. Explicit `yes` is required.

---

## ✏️ Editing the Summary

Refine the output before sending:

```
edit: make it shorter
```

```
edit: focus more on user impact
```

```
edit: make it more suitable for a non-technical client
```

The skill regenerates based on your feedback.

---

## 🧩 Example Workflow

### Input

```
summarize this diff
```

*(diff includes search improvements and bug fixes)*

---

### Step 0 — Audience question

```
Who is the intended reader of this summary?
```

```
PM at a product company, no technical background
```

---

### Step 1 — Destination resolved

```
I found Linear issue ABC-123 from your branch name. I'll post there unless you say otherwise.
```

---

### Output (preview)

````markdown
```markdown
## 📝 Summary
The search experience got faster and more reliable. Users will notice it immediately.

## 🚀 User Impact
Finding things is quicker. Fewer dead ends when navigating results.

## 🔧 Improvements
- Results appear faster while typing
- Navigation between results is more stable
- Fewer errors when the list updates
```
````

---

### Confirmation

```
Do you want me to post this to Linear issue ABC-123?
```

---

### Final Step

```
yes
```

✅ The summary is posted to Linear as a comment.

---

### Alternative — Copy only

```
copy
```

The summary is already in the block above. No posting happens. Done.

---

## 🧠 Best Practices

### ✅ Do

* Specify your audience — it makes a visible difference in tone
* Use branch naming like `feature/ABC-123-add-search` for auto-detection
* Review the summary before sending
* Use `edit:` freely — it's fast to iterate

### ❌ Don't

* Send summaries without reviewing them
* Skip the audience question (default works but specific beats generic)
* Use `yes` without reading the preview

---

## 🛡️ Safety

* The skill **never posts automatically**
* Requires explicit `yes` confirmation before any MCP call
* Prevents accidental updates to wrong issues or platforms

---

## 📌 Summary

This workflow ensures every change:

* Is clearly communicated to the right audience
* Is understandable by non-technical stakeholders
* Is properly documented in your issue tracker (or ready to paste anywhere)
