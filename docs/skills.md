# Skills

Skills are structured markdown files that give AI agents domain-specific knowledge and repeatable workflows for bounded tasks.
Unlike steering (which sets tone and constraints) or agents (which define tools and personality), a skill is a portable, self-contained "how to do X" that any compatible agent can pick up.

Skills in this repo use the `SKILL.md` format supported by Kiro and ship with the kit.
They get copied into `~/.kiro/skills/` by the sandbox startup command.

## Where skills live

```
di-kit/files/home/di-kit/
├── shared/.kiro/skills/       ← Ships with the kit (everyone gets these)
│   └── dependabot-pr-review/
│       └── SKILL.md
└── personal/.kiro/skills/     ← User overrides (gitignored, not shared)
```

Shared skills are team defaults.
Personal skills let individuals override or extend without affecting the kit for others.

> **Future consideration:** if we have multiple kits, skills may need to live at a level above and be symlinked or referenced into each kit.
> For now, one kit — keep it simple.

## Anatomy of a skill

A skill is a folder containing a `SKILL.md` file:

```
my-skill/
├── SKILL.md           # Required — instructions and workflow
├── scripts/           # Optional — deterministic automation
├── references/        # Optional — detailed docs loaded on demand
└── assets/            # Optional — templates, examples
```

### SKILL.md format

```markdown
---
name: my-skill-name
description: One-line trigger description — when should an agent use this?
---

# Skill Title

Instructions, workflow steps, and decision logic here.
```

### Frontmatter fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Must match folder name. Lowercase, numbers, hyphens only. Max 64 chars. |
| `description` | Yes | When to use this skill. The agent matches this against user requests. Max 1024 chars. |
| `license` | No | License name or reference. |
| `compatibility` | No | Environment requirements (tools, network access). |
| `metadata` | No | Additional key-value data (author, version). |

### How activation works

1. **Discovery** — at startup, only `name` and `description` from each skill are loaded.
2. **Activation** — when the user's request matches a description, the full `SKILL.md` is loaded.
3. **Execution** — the agent follows instructions, loading reference files only as needed.

This progressive disclosure keeps context focused.
Write descriptions that trigger on the right prompts.

## Principles for good skills

### 1. Bounded scope

One task, not a Swiss army knife.
A skill for reviewing Dependabot PRs is good.
A skill that also manages release branches, writes changelogs, and deploys is trying to do too much.

If you need multiple skills to compose, that's fine — keep each one coherent and let the user chain them.

### 2. Concise over comprehensive

Skills are injected into the agent's context window alongside conversation history, system prompts, and other active skills.
Every token competes for attention.

- **Add what the agent lacks, omit what it knows.** Don't explain what a PR is or how HTTP works. Do explain your team's specific conventions, edge cases, and tool preferences.
- **Challenge each paragraph:** "Would the agent get this wrong without this instruction?" If no, cut it.
- **Target:** keep `SKILL.md` under 500 lines. Move detailed reference material to `references/` with clear instructions on when to load it.

### 3. Defaults over menus

When multiple tools or approaches could work, pick one default and mention alternatives briefly.
Don't present equal-weight options that force the agent to choose.

```markdown
<!-- Bad: too many options -->
You can use gh, or curl with the API, or the GitHub MCP tool...

<!-- Good: clear default with escape hatch -->
Use the GitHub API with curl. If the API ping fails (401/403), fall back to `gh`.
```

### 4. Procedures over declarations

Teach the agent *how to approach* a class of problems, not *what to produce* for one instance.
The approach should generalise even when individual details are specific.

### 5. Portable across environments

Skills should work in the sandbox, local Kiro, or CI without modification.
Avoid hardcoding paths, tokens, or environment-specific assumptions.
Detect the environment and adapt.

### 6. Ecosystem-aware

Reference actual tools and manifests for our stack:

| Language | Package manager | Manifest | Lockfile |
|----------|----------------|----------|----------|
| Kotlin | Gradle | `build.gradle.kts`, `libs.versions.toml` | `gradle.lockfile` |
| Java | Gradle or Maven | `build.gradle.kts` or `pom.xml` | `gradle.lockfile` or resolved POM |
| Swift | SPM | `Package.swift` | `Package.resolved` |
| TypeScript | npm | `package.json` | `package-lock.json` |

### 7. Opinionated with escape hatches

Give a clear default action but explain when to escalate.
Hard gates (like "never merge with failing CI") should be unambiguous.
Softer judgments (like "likely safe but verify X") should name the specific check.

## Writing effective descriptions

The `description` field is how the agent decides whether to activate your skill.
Get it right:

- **Be specific.** Include concrete trigger keywords. "Review Dependabot pull requests for security, compatibility, and merge readiness" beats "helps with PRs."
- **Write in third person.** The description is injected into the system prompt. "Reviews pull requests..." not "I can help you review..."
- **Include both what and when.** "Review Dependabot PRs. Use when asked to assess, triage, approve, or merge dependency update PRs."

## Structuring workflows

Good skills follow a consistent pattern:

1. **Modes** — what variants of the task exist (single item vs batch, quick vs thorough).
2. **Access strategy** — how to get the data (API, CLI, filesystem) with fallback ordering.
3. **Workflow steps** — sequential process with decision points.
4. **Hard gates** — things that must be true before proceeding (CI passing, cooldown met).
5. **Output format** — templates for what the result looks like.
6. **Explicit non-goals** — what the skill deliberately does NOT do.

### Gotchas sections

The highest-value content is often a list of gotchas — environment-specific facts that defy reasonable assumptions:

```markdown
## Gotchas

- Gradle version catalogs (`libs.versions.toml`) declare versions centrally
  but the dependency may be used in subprojects — search all `build.gradle.kts` files.
- npm workspaces hoist dependencies to the root `node_modules` — a dependency
  in a workspace `package.json` may not have its own lockfile entry.
- Pre-1.0 semver minors (0.x.y → 0.x+1.0) are breaking-change equivalent.
```

### Validation loops

Instruct the agent to validate its own work before moving on:

```markdown
1. Gather data
2. Analyse and draft verdict
3. Cross-check verdict against hard gates
4. If any gate fails, revise verdict
5. Present result
```

### Output templates

Provide concrete templates rather than describing format in prose.
Agents pattern-match well against structure:

```markdown
## Output Format

### Recommendation
[Merge / Verify / Investigate / Hold] — [1-3 sentences with reason and specific check]
```

## Scripts and automation

Use scripts for deterministic tasks.
Pre-made scripts are more reliable than asking the agent to generate code each time, save tokens, and ensure consistency.

```
my-skill/
└── scripts/
    └── validate.sh    # Agent executes this, doesn't load it into context
```

Make clear whether the agent should **execute** the script or **read** it as reference:
- "Run `scripts/validate.sh` to check the output" → execute
- "See `scripts/validate.sh` for the validation algorithm" → read as reference

## Testing and iteration

1. **Run the skill against real tasks** before considering it done.
2. **Read execution traces**, not just final output. If the agent wastes time on unproductive steps, the skill may be too vague or present too many options.
3. **Add corrections to a gotchas section** when the agent makes mistakes you have to fix.
4. **Iterate.** Even one pass of execute-then-revise noticeably improves quality.

## References

These resources informed the conventions in this document:

- [Kiro: Agent Skills](https://kiro.dev/docs/skills/) — how skills work in Kiro (progressive disclosure, activation, scope)
- [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — conciseness, degrees of freedom, evaluation-driven development
- [Agent Skills: Best practices for skill creators](https://agentskills.io/skill-creation/best-practices) — context budgets, gotchas, validation loops, scripts
- [OpenAI Academy: Using skills](https://openai.com/academy/skills/) — repeatable workflows, building blocks, input/output patterns

## Checklist before merging a new skill

- [ ] `name` matches folder name, lowercase with hyphens
- [ ] `description` is specific, includes trigger keywords, under 1024 chars
- [ ] `SKILL.md` body is under 500 lines
- [ ] Detailed reference material is in separate files (if needed)
- [ ] No hardcoded secrets, tokens, or user-specific paths
- [ ] Works in sandbox environment without modification
- [ ] Tested against at least one real scenario
- [ ] Hard gates are unambiguous
- [ ] Output format has a concrete template
- [ ] Non-goals are explicit
