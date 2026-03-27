---
name: git-integration
description: Git operations - commits, branches, PRs, code review automation
category: development
tags: [git, github, version-control, automation]
---

# Git Integration Skill

Automate Git workflows and GitHub operations.

## Capabilities

- Repository initialization and cloning
- Branch management
- Commit automation with AI-generated messages
- Pull request creation and review
- Code diff analysis
- Merge conflict resolution suggestions
- GitHub Actions integration
- Release management

## Usage

```python
from skills.git_integration import GitManager

git = GitManager()

# Initialize repo
git.init_repo("/path/to/project")

# Smart commit
git.smart_commit("/path/to/project", "Added user authentication")

# Create PR
git.create_pr(
    repo="owner/repo",
    title="Feature: Add authentication",
    body="Description...",
    head_branch="feature/auth",
    base_branch="main"
)
```
