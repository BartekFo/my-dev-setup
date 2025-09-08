---
description: Create PR in repo using GitHub CLI
allowed-tools: Bash(gh:*, git:*), Write, Read
---

Create a pull request using the GitHub CLI with proper formatting.

Steps to follow:

1. **Check current branch and base branch:**
!git branch --show-current > /dev/null 2>&1
!git log --oneline --graph --decorate -10 > /dev/null 2>&1

2. **Determine base branch from git log:**
Analyze the git log to determine what branch the current branch was created from (likely `main` or `staging` based on the project).

3. **Get recent commits for context:**
!git log --oneline -5 > /dev/null 2>&1

4. **Generate PR title:**
Create a concise, descriptive title based on the recent commits and branch name.

5. **Create PR description:**
Create a bulleted list of changes in markdown format. Follow this template structure:

```markdown
# Issue: CON-[TICKET_NUMBER]

## 📝 Description

[Brief summary of changes]

### Changes Made:
- [Bullet point of change 1]
- [Bullet point of change 2]
- [Bullet point of change 3]

## ✅ Before submitting my PR, I have made sure that:

- **I have performed a self-review of my own code.**
- My code follows the style guidelines of this project.
- My changes generate no new errors.
- I have tested my changes locally.
- I have added tests for new features or bug fixes.
- I have verified that existing tests pass.
- I have commented my code, particularly in hard-to-understand areas.
- I have made corresponding changes to the documentation.
- I have ensured no sensitive information (e.g., keys, credentials) is included.
```

6. **Create temporary markdown file:**
Write the PR description to a temporary file `/tmp/pr-description.md`

7. **Create the PR:**
!gh pr create --title "[GENERATED_TITLE]" --body-file /tmp/pr-description.md --base [BASE_BRANCH] > /dev/null 2>&1

8. **Clean up:**
!rm /tmp/pr-description.md > /dev/null 2>&1

Make the PR title short, descriptive, and professional. Extract the ticket number from the branch name if present.