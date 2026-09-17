---
name: incremental-commits
description: Make small, atomic git commits as development progresses, validating tests and lint before each and getting user approval before committing. Use when asked to "commit as you go", "make small commits", "checkpoint work", or when a task plan specifies commit checkpoints.
---

# Incremental Commits

Make small, atomic commits throughout a development task. Each commit is self-contained, passes
lint and tests, and tells a story. Never commit without the user's explicit approval.

## When to activate

This skill applies when:

- The user asks you to "commit as you go", "make small commits", or "checkpoint work"
- A task plan includes commit checkpoints
- The user explicitly says to use this workflow

It does NOT activate by default on every coding task. The user opts in.

## Detect project tooling

Before making any commit, discover the project's validation commands. Check for:

| File                      | Likely commands                                                  |
| ------------------------- | ---------------------------------------------------------------- |
| `package.json`            | `scripts.test`, `scripts.lint`, `scripts.check`, `scripts.build` |
| `Makefile`                | `make test`, `make lint`, `make check`                           |
| `build.gradle.kts`        | `./gradlew check`, `./gradlew test`                              |
| `pom.xml`                 | `mvn verify`                                                     |
| `Cargo.toml`              | `cargo test`, `cargo clippy`                                     |
| `Package.swift`           | `swift test`                                                     |
| `.pre-commit-config.yaml` | `pre-commit run --all-files`                                     |

If multiple exist, use the most comprehensive check (e.g. `./gradlew check` over `./gradlew test`
alone). If unclear, ask the user which commands validate their code.

Cache the commands for the session — don't re-discover before every commit.

## What makes an atomic commit

Each commit must be:

1. **Self-contained** — implements one logical step; the codebase is coherent before and after
2. **Focused** — only includes changes that achieve that step
3. **Ordered** — commits build on each other logically; they tell a story

Good commit boundaries:

- A function and its tests
- A refactoring that moves code without changing behaviour
- A configuration change
- A bug fix with its regression test
- Adding a dependency and the code that uses it

Bad commit boundaries:

- Half-finished work that doesn't compile
- Multiple unrelated fixes lumped together
- Tests separated from the code they test
- A refactoring mixed with a behaviour change

When in doubt: could someone read just this diff and understand the complete intent? If not, split
or combine.

## Workflow

### 1. Complete a logical unit of work

Do the coding work. When you reach a natural checkpoint — one idea fully implemented — pause.

### 2. Validate

Run the project's lint and test commands (discovered above). Example for a Node.js project:

```bash
npm run lint
npm test
```

If validation fails, fix the issues before proposing the commit. Do not present a failing commit
to the user.

### 3. Stage selectively

Stage only the files relevant to this logical unit:

```bash
git add <specific-files>
```

Never use `git add .` or `git add -A` unless every changed file genuinely belongs in this commit.
If unrelated changes exist in the working tree, leave them unstaged.

Check what you're about to propose:

```bash
git diff --cached --stat
git diff --cached
```

### 4. Draft the commit message

Write a message following these rules.

**Subject line:**

- Maximum 50 characters
- Imperative mood ("Add feature" not "Added feature") — imagine a silent "please" before it
- Capitalised first word
- No full stop at the end

**Body (when the "what" isn't self-explanatory):**

- Separated from subject by a blank line
- Wrapped at around 72 characters
- Explains the **why**, not just the what — the diff already shows what changed
- Captures context a future reader would otherwise lose (like an ADR)

A link to a ticket is **not** a substitute for a message. The message must stand on its own —
links can break, and the reasoning must survive.

For the rationale behind these rules, worked examples, and the source blog posts, see
`references/sources.md` (load on demand — don't read it unless you need the background).

Example:

```
Set cache headers for static assets

IE 6 was caching responses aggressively, causing stale content
to appear after deployments. Adding Cache-Control: no-cache on
HTML responses fixes this while keeping assets cacheable.

See https://example.com/ie6-caching for background.
```

### 5. Present the checkpoint

Show the user:

```markdown
## Commit checkpoint

**Proposed message:**

> Subject line here
>
> Body here (if applicable)

**Staged changes:**

- path/to/file1.ts (modified)
- path/to/file2.ts (new)
- path/to/file2.test.ts (new)

**Validation:** ✓ lint passed, ✓ tests passed (N tests, Ns)

<diff summary, plus full diff if short or key excerpts if long>

Ready to commit? You can:

- **approve** — commit as proposed
- **edit** — suggest a different message or staging
- **split** — break this into smaller commits
- **skip** — leave changes uncommitted for now
- **discuss** — ask questions or raise concerns
```

### 6. Wait for explicit approval

Do NOT commit until the user says yes. If they want changes:

- **Edit message** — adjust and re-present
- **Split** — unstage some files, commit the rest first, then propose the remainder
- **Discuss** — answer questions, explain reasoning, adjust approach

### 7. Commit

Only after approval:

```bash
git commit -m "Subject line" -m "Body paragraph"
```

For multi-paragraph bodies, write the message to a temp file and use `git commit -F <file>` (then
clean up the temp file).

Confirm the commit was made:

```bash
git log --oneline -1
```

Then continue with the next unit of work.

## Hard gates

- **Never** commit with failing tests or lint. Fix first, then propose.
- **Never** commit without user approval. Always present and wait.
- **Never** force-push or amend without explicit permission.
- **Never** stage unrelated changes in the same commit.
- **Never** use a ticket link as a substitute for a descriptive commit message.
- **Respect pre-commit hooks.** If they exist, let them run. Do not use `--no-verify`.

## Handling edge cases

**Tests don't exist yet** — if the project has no test infrastructure, validation is lint-only (or
build-only). Note this when presenting: "No test suite found — validated with lint/build only."

**Changes span many files** — atomic doesn't mean small in line count; it means self-contained in
purpose. A rename touching many files is fine. Present the full scope and let the user decide
whether to split.

**User wants to batch** — if the user says "just commit everything at the end", respect that. This
skill is opt-in. Suggest the incremental approach but don't insist.

**Conflicts with uncommitted work** — if there are unstaged changes from earlier work when starting
a new unit, flag it: "There are uncommitted changes from before — commit those first, stash them,
or include them?"

## Non-goals

- Does not push to a remote (the user decides when to push)
- Does not create branches (work on whatever branch the user is on)
- Does not write PR descriptions (separate concern)
- Does not enforce a commit prefix/convention beyond the format rules above
- Does not rebase, squash, or rewrite history
