---
name: github-pull-requests
description: Help write or review a GitHub pull request description. Use when asked to draft a PR, write a PR description, check how a PR links to an issue, decide whether to use a closing keyword, or assess whether an issue is scoped correctly for a PR.
metadata:
  author: "@huwd"
  version: "1.0.0"
---

# GitHub Pull Requests

Help developers write clear, well-linked pull request descriptions that accurately represent the relationship between the PR and the work being tracked.

The guiding principle: a PR is a unit of review, not a unit of deployment. Its description should give a reviewer enough context to understand what changed, why, and what to look for — without having to read every commit.

References: [GDS Way: Working with Git](https://gds-way.digital.cabinet-office.gov.uk/standards/source-code/working-with-git.html), [Anna Shipman: Good pull requests](https://www.annashipman.co.uk/jfdi/good-pull-requests.html), [One Pull Request. One Concern.](https://fagnerbrack.com/one-pull-request-one-concern-e84a27dfe9f1)

## Choose a Mode

- **Draft mode**: the user wants help writing a PR description. Read the branch's commit log and diff summary if not provided.
- **Review mode**: the user wants an existing PR description checked for completeness, clarity, and correct issue linking.

If ambiguous, default to draft mode.

## PR Description Structure

A good PR description answers three questions for the reviewer:

1. **What changed?** — a plain-language summary of the change. Not a restatement of the commit log; a human-readable overview.
2. **Why?** — the motivation. Link to the issue, but also state the reason in plain text so the description stands on its own if the issue link breaks.
3. **What to look for?** — any areas of particular interest, tradeoffs made, things that might look surprising, or manual checks the reviewer should perform.

Keep it proportionate. A one-line typo fix needs one line. A significant feature warrants a paragraph per section.

### Template

```markdown
## What

[Plain-language summary of the change — not a restatement of the commit log.]

## Why

[Motivation for the change. Should stand on its own even if the issue link breaks.]

## Notes for reviewers

[Optional. Tradeoffs, areas of particular interest, surprising decisions, manual checks.]
```

Not every PR needs all three sections. Small PRs can use a single paragraph. Use judgment.

## Issue Linking

How a PR links to an issue communicates something specific. Get it right.

### Closing keywords — use when the PR fully resolves the issue

```
Closes #N
Fixes #N
Resolves #N
```

When merged, GitHub automatically closes the linked issue. Use this **only** when the PR completes all the work described in the issue.

### Partial-fix references — use when work remains

```
Refs #N
Part of #N
Related to #N
```

These reference the issue without closing it. Use when the PR addresses part of an issue but leaves work outstanding.

**Why this matters**: using `Closes` on a partial fix silently marks unfinished work as done. Future developers (and your future self) lose the thread.

### No issue — acceptable but limited

If there is no issue, omit the linking line. Consider whether the work should have an issue — PRs without issue context make it harder to understand the intent months later.

## Issue Granularity Signal

If partial-fix PRs against the same issue keep accumulating, that is a signal the issue is too coarse-grained.

When you see this pattern, flag it:

> This is the second/third partial-fix PR against #N. Consider splitting #N into sub-issues so each piece of work can be tracked and closed independently.

Split issues before the next PR, not after. Discovering the split mid-PR is a signal; acting on it up front keeps the tracker honest.

## Draft Workflow

1. Read the branch's commit log (`git log --oneline origin/main..HEAD`) and a summary of the diff.
2. Identify whether the PR fully resolves an issue or partially addresses one.
3. Draft the description using the template above. Scale the detail to the size of the change.
4. Choose the correct issue-linking syntax (`Closes`, `Refs`, or none).
5. If a partial-fix pattern is apparent, flag the issue granularity signal.
6. Present the draft. Explain the linking choice if it is not the obvious one.

## Review Workflow

1. Read the existing PR description.
2. Check: does it answer what changed, why, and what to look for?
3. Check issue linking: is the correct keyword used? Would merging close issues that are not fully resolved?
4. Check for the partial-fix accumulation pattern if there is history of prior PRs against the same issue.
5. Report findings. For each problem, state what is missing or wrong and suggest a fix.

## Gotchas

- `Closes` and `Fixes` are functionally identical on GitHub — both close the issue on merge. Prefer `Closes` for features, `Fixes` for bugs — it reads more naturally.
- Closing keywords only work in the PR description, not in commit messages or comments, for the auto-close behaviour on GitHub.
- A PR description that just says "See #N" is not sufficient — the issue may be deleted, made private, or the link may rot. Summarise the why in the PR body.
- Draft PRs: mark a PR as draft if it is not ready for review. This is not a convention to enforce here, but worth flagging if a user opens a PR for early feedback.
- Squash merges on GitHub create a single commit from all PR commits. If the project uses squash merges, the PR title becomes the commit subject — apply the same Conventional Commits format to PR titles as to commit subjects. See the `git-workflow` skill.

## Explicit Non-Goals

- Does not cover PR review behaviour (giving or receiving feedback) — tracked in issue #28.
- Does not assess code quality or test coverage — that is CI and the reviewer's job.
- Does not manage merge strategy — that is a repo-level decision.
- Does not cover commit message quality within the PR — see the `git-workflow` skill.
