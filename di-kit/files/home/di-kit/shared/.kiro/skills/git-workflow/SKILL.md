---
name: git-workflow
description: Help write, review, or explain git commits and branch names to GDS and Conventional Commits standards. Use when asked to write a commit message, name a branch, check commit history, tidy a branch before a PR, or explain why commits should be structured a certain way.
metadata:
  author: "@huwd"
  version: "1.0.0"
---

# Git Workflow

Help developers produce clean, meaningful git history: well-formed commits, consistent branch names, and tidy branch history before sharing.

The guiding principle: commit history is the most reliable documentation a codebase has — it is always current, searchable, and kept forever. The diff shows *how* a change was made; only the commit message captures *why*. Protect the why.

References: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), [GDS Way: Working with Git](https://gds-way.digital.cabinet-office.gov.uk/standards/source-code/working-with-git.html), [Joel Chippindale: Telling stories through your commits](https://blog.mocoso.co.uk/posts/talks/telling-stories-through-your-commits/)

## Choose a Mode

- **Draft mode**: the user wants help writing a commit message or branch name. Ask for the staged diff or a description of the change if not provided.
- **Review mode**: the user wants commits or a branch reviewed against the standard. Inspect the actual git log or branch name.
- **Explain mode**: the user wants to understand why these conventions exist or how to apply them.

If the request is ambiguous, default to draft mode.

## Commit Standard

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Use for |
|------|---------|
| `feat` | New feature (correlates with semver MINOR) |
| `fix` | Bug fix (correlates with semver PATCH) |
| `docs` | Documentation only |
| `style` | Formatting, whitespace — no logic change |
| `refactor` | Code change that is neither a fix nor a feature |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `build` | Build system or dependency changes |
| `ci` | CI configuration changes |
| `chore` | Maintenance tasks that don't fit elsewhere |

Breaking changes: append `!` after type/scope (`feat!:`) **and/or** add a `BREAKING CHANGE:` footer.

### Subject line rules

- Max 50 characters
- Imperative mood: "Add feature" not "Added feature" or "Adding feature"
- No trailing period
- Leading lowercase after the colon (the type prefix handles capitalisation)

A useful test: the subject should complete the sentence "If applied, this commit will _____."

### Body (required for anything non-trivial)

- Separated from subject by a blank line
- Wrapped at 72 characters
- Answer three questions:
  1. **Why** is this change necessary?
  2. **How** does it address the issue?
  3. What **side effects** might it have?
- Note alternatives considered — future developers will want to know why approach A was chosen over B
- The diff shows the *how*; the body captures the *why*, which is impossible to reconstruct later

### Atomicity

Each commit must be a single logical unit. Err towards too many commits rather than too few.

Three tests for atomicity — if any of these trigger, consider splitting:

**The "and" test**: if you need "and" in the subject line, it is probably two commits. "Add user auth and update session handling" is two changes.

**The cherry-pick/revert test**: could you cleanly `git cherry-pick` or `git revert` this commit without accidentally carrying or undoing unrelated work? A commit that bundles two concerns cannot be reverted to just one of them. Each commit should be a unit you could drop, revert, or transplant without side effects.

**The "also" test**: when writing the body to explain *why*, if you find yourself using "also" — "this was necessary because X, and also because Y" — that is a signal the commit is doing two things for two different reasons. Split at the "also".

The goal is commits that are easy to review and tell a clear story. A reviewer reading your branch commit-by-commit should feel like they are reading a book: each commit is a short, self-contained chapter. They should be able to follow the narrative without holding the whole diff in their head at once.

A commit does not need to be small — it needs to be *coherent*. A refactor touching 50 files is one atomic commit if it makes one change for one reason. But two independent features in the same file are still two commits.

### Draft Workflow

1. Read the diff (staged changes or the description provided).
2. **Atomicity check first**: apply the three tests. Does the subject need "and"? Could this be cleanly reverted without side effects? Does explaining *why* require "also"? If any test triggers, stop and propose how to split before drafting a message — a well-formed message on a non-atomic commit is still wrong.
3. Determine the correct type from the table above.
4. Draft a subject line: ≤50 chars, imperative, no period.
5. If the change is non-trivial, draft a body answering the three questions. The body should read like one short chapter — self-contained, not needing context from the previous or next commit to make sense.
6. Add footers if needed: `BREAKING CHANGE:`, `Closes #N`, `Refs #N`.
7. Present the full commit message. Explain any choices that are not obvious.

### Review Workflow

1. Read the commit message(s) to review.
2. Check each rule in order: type valid, subject ≤50 chars, imperative mood, no trailing period, blank line before body, body wrapped at 72 chars.
3. Check whether a body is present for non-trivial commits. If absent, flag it.
4. Check for atomicity using all three tests: does the subject need "and"? Could it be cleanly reverted? Does the body use "also" to explain two different reasons? Flag each violation with a suggested split.
5. Report findings per commit. For each violation, state the rule, the problem, and a suggested fix.

## Branch Naming Standard

Format: `<type>/<issue-number>-<short-description>`

The issue number is optional when there is no tracker. The type must match a valid commit type.

```bash
# Examples
feat/42-add-user-auth
fix/17-nil-pointer-on-logout
chore/update-dependencies
ci/29-add-coverage-upload
docs/readme-setup-steps
```

### Rules

- Type must be a valid commit type from the table above
- Short description: lowercase, hyphens for spaces, no special characters
- Keep it short enough to scan in a branch list — aim for under 50 characters total
- Never commit directly to `main`

### Branch Draft Workflow

1. Confirm the type of work (feat, fix, chore, etc.).
2. Ask for the issue number if there is a tracker and it was not provided.
3. Derive a short description from the change or issue title — lowercase, hyphens.
4. Present the full branch name with the `git checkout -b` and `git push -u` commands ready to run.

## History Tidying (before opening a PR)

Before a branch is ready for review, its history should tell a coherent story of what was *intended*, not a log of every misstep along the way.

Use `git rebase -i` to:
- **Squash** fixup commits into the commit they correct (`fixup` or `squash`)
- **Reorder** commits so the narrative flows logically
- **Edit** commit messages that were written hastily mid-work
- **Split** a commit that grew to cover multiple concerns

The rule: rewriting is fine on your own branch before sharing. Once commits are on `main` or visible to others, do not rewrite them.

```bash
# Rebase interactively from the point the branch diverged from main
git rebase -i origin/main
```

When asked to help tidy a branch, read `git log --oneline origin/main..HEAD` first to see the shape of the work, then suggest a rebase plan before the user runs it.

## Gotchas

- `style:` is for whitespace and formatting only — no behaviour changes. A linter fix that also changes a default is `fix:`, not `style:`.
- `chore:` is a catch-all of last resort. If a more specific type fits, use it.
- Scope (the part in parentheses) is optional but useful in monorepos or multi-package repos: `feat(auth):`, `fix(api):`. Use it consistently or not at all — mixing scoped and unscoped commits in the same repo is confusing.
- `git rebase -i` rewrites history. Never rebase commits already on `main` or shared with others.
- A subject over 50 characters will be truncated in GitHub's commit list. Write the full detail in the body.
- Pre-1.0 semver: a `feat:` on a 0.x.y project still correlates with a minor bump, but treat 0.x → 0.x+1 as breaking-change equivalent in practice.

## Explicit Non-Goals

- Does not enforce CI or test requirements — that is the verification loop in the project's workflow.
- Does not manage merging strategy (squash merge, merge commit, rebase merge) — that is a repo-level decision.
- Does not cover PR authoring — see the `github-pull-requests` skill.
