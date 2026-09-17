# References — Incremental Commits

Sources that inform the atomic-commit and commit-message conventions in `SKILL.md`.
Load this file when you need the underlying rationale, worked examples, or want to point a user at
the original guidance.

## Atomic commits — telling a story

- [Anna Shipman: Good pull requests — make the pull request tell a story](https://www.annashipman.co.uk/jfdi/good-pull-requests.html#make-the-pull-request-tell-a-story)
  — the principle that a series of small, ordered commits communicates intent far better than one
  large diff.
- Worked example: a [single commit with 51 files changed](https://github.com/alphagov/paas-alpha-tsuru-ansible/commit/7547ac0d35a)
  was broken down into a [series of 8 commits](https://github.com/alphagov/paas-alpha-tsuru-ansible/compare/d891857...d14bb2f44)
  implementing the same change.

## Commit messages — structure and content

- [Chris Beams: How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
  — the seven rules (50-char imperative subject, blank line, 72-char body, explain *why*).
- [Tim Pope: A note about git commit messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
  — the canonical subject/body format the subject-line rules derive from.
- [thoughtbot: 5 useful tips for a better commit message](https://thoughtbot.com/blog/5-useful-tips-for-a-better-commit-message)
- [Mislav Marohnić: Every line of code is always documented](https://mislav.net/2014/02/hidden-documentation/)
  — commit history as living documentation for *why* a change was made.

## Capturing the "why"

- [Cognitect: Documenting architecture decisions (ADRs)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
  — the same motivation behind explaining *why* in a commit body: preserving decision context for
  future readers.

## GDS Way

The commit guidance in `SKILL.md` follows the GDS Way "Commits" conventions (atomic commits,
imperative 50-char subject, 72-char wrapped body, explain the why, ticket links are not a
substitute for a message).
