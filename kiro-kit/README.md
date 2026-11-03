# AWS IAM SBX Kit

## Quick start

```bash
# One-time setup: allow kits from ghcr.io/govuk-one-login
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'

# Run the sandbox with the latest published kit
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/kiro-kit:latest
```

To pin to a specific version:

```bash
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/kiro-kit:1.0.0
```

## Local development

When iterating on the kit itself, use the local path:

```bash
# Validate the kit
sbx kit validate kiro-kit

# Run from local directory
sbx run di-kiro . --kit kiro-kit
```

## Releasing

1. Bump the version in `kiro-kit/.kit_version`
2. Update `kiro-kit/CHANGELOG.md` with what changed
3. Merge to main — CI publishes automatically

CI will:
- Validate the kit
- Push `ghcr.io/govuk-one-login/ai-sandbox/kiro-kit:<version>` and `:latest`
- Tag the commit as `kiro-kit/v<version>`
- Create a GitHub Release with auto-generated notes

The publish only fires when `.kit_version` contains a version that hasn't been tagged yet, so merging doc-only changes won't trigger a release.

A manual **workflow_dispatch** trigger is available as a fallback if needed (Actions → Publish kits → Run workflow on `main`).

## Configuration

- **AWS Region**: eu-west-2
- **SSO URL**: https://uk-digital-identity.awsapps.com/start/#/
- **Network Access**:
  - `management.eu-central-1.kiro.dev:443`
  - `runtime.eu-central-1.kiro.dev:443`

## Kiro Config

The kit supports shared organisation config and personal overrides, both delivered to `~/.kiro/` (global Kiro config) in the sandbox.

### Shared config (committed)

Shared config lives in `kiro-kit/files/home/kiro-kit/shared/.kiro/` and is committed to the repo.

```
kiro-kit/files/home/kiro-kit/shared/.kiro/
├── agents/
│   ├── code-explainer.json
│   ├── code-planner.json
│   ├── self-improve.json
│   └── shakespeare-example.json
├── settings/
│   ├── .kiroignore
│   └── permissions.yaml
└── steering/
    ├── code-committer.md
    ├── code-explainer.md
    ├── code-planner.md
    └── self-improve-prompt.md
```

### Personal config (not committed)

Personal config lives in `kiro-kit/files/home/kiro-kit/personal/.kiro/` and overrides shared config. This directory is gitignored — create it manually and add your own config.

### How it works

1. The kit's `files/home/` mechanism delivers `kiro-kit/shared/` and `kiro-kit/personal/` (if it exists) to `/home/agent/kiro-kit/` in the container
2. A startup command copies `/home/agent/kiro-kit/shared/.kiro/` into `~/.kiro/`
3. A startup command installs the shared agent skills (see [Agent skills](#agent-skills)) into `~/.kiro/skills/` from [govuk-one-login/agent-skills](https://github.com/govuk-one-login/agent-skills)
4. A final startup command copies `/home/agent/kiro-kit/personal/.kiro/` over `~/.kiro/`

Shared is applied first, then personal overlays on top. This uses Kiro's global steering — config in `~/.kiro/` applies to all workspaces in the sandbox.

### Included agents

- **code-explainer** — Explains code and architecture using git history
- **code-planner** — Creates structured implementation plans
- **self-improve** — Reflects on feedback and improves the agent suite
- **shakespeare-example** — Demo agent responding in Shakespearian prose

### Switching agents in the sandbox

Once inside the sandbox, switch to a custom agent with:

```
/agent swap
```

Then select an agent from the list.

## Agent skills

Skills are **not** committed to this kit. At sandbox startup,
[Agent Manager](https://github.com/ai-agent-manager/agent-manager) installs the
skills listed in `files/home/kiro-kit/shared/ai-skills.yml` into
`~/.kiro/skills/`, pulling them from the source repositories declared in the
[govuk-one-login/agent-skills](https://github.com/govuk-one-login/agent-skills)
discovery document.

- **Change the skill set**: edit the `skills:` list in `ai-skills.yml`. The
  available skills are listed in the agent-skills README (and the CLI's
  interactive menu shows them all: `npx -y @ai-agent-manager/cli@latest
  govuk-one-login/agent-skills` without `--config`).
- **Adding a new skill**: contribute it to one of the source repositories
  (marketplace layout, `skills/<name>/SKILL.md`), then add its name to
  `ai-skills.yml`.
- **Pinning**: the install uses the latest CLI and the default branch of each
  source. To pin the discovery document to a branch or tag, point the remote
  at `https://github.com/govuk-one-login/agent-skills/tree/<ref>` in the
  startup command in `spec.yaml`.
- **Troubleshooting**: the install runs as a startup command, so failures
  show in `sbx logs` / `sbx status`. The GitHub hosts it needs are in the
  network allow list in `spec.yaml` — check `sbx policy log` after a failure.

### dependabot-pr-review

This skill reads PR metadata, CI status, and diffs via the GitHub API.
It can optionally post review comments and merge PRs when explicitly approved by the user.

| Permission | Scope | Why |
|------------|-------|-----|
| `pull_requests: read` | Repository | List open PRs, read metadata, diffs, and changed files |
| `checks: read` | Repository | Read CI check-run status for PR head commits |
| `issues: read` | Repository | Read PR comments (to detect existing review markers) |
| `pull_requests: write` | Repository | Post review comments and merge PRs (optional — only used with user approval) |
| `issues: write` | Repository | Post comments on PR issue threads (optional — only used with user approval) |
| `contents: read` | Repository | Read `.github/dependabot.yml`, manifests, and source files for codebase impact analysis |

**Recommended token type:** fine-grained personal access token (PAT) scoped to the specific repository or repositories you want to review.

**Read-only mode:** if you only want the skill to analyse and report (never post or merge), you can omit the `write` permissions entirely.
The skill will still produce full reviews — it just won't be able to act on them.

### Setting up GitHub access with sbx

The sandbox proxy authenticates API requests on behalf of the agent — the token is never exposed directly inside the sandbox.

1. Create a fine-grained PAT: [GitHub → Settings → Developer settings → Fine-grained tokens](https://github.com/settings/tokens?type=beta), with the resource owner set to the org or account that owns the repos, repository access limited to the repos you want to review, and the permissions from the table above.
2. Store the token with sbx:

   ```bash
   # Global — available to all sandboxes on this machine
   sbx secret set -g github

   # Or scoped to a specific sandbox
   sbx secret set <sandbox-name> github

   # Or pipe it from a secret manager
   gh auth token | sbx secret set -g github
   ```
3. Verify with `sbx secret ls` — you should see `github` listed with the appropriate scope.

When the sandbox starts, the sbx proxy intercepts requests to `api.github.com` and attaches the stored token automatically.
The skill's API-first approach (`curl` to `api.github.com`) works without any `Authorization` header in the commands — the proxy handles it transparently.
If no GitHub secret is configured, the skill falls back to the `gh` CLI command set, which uses whatever authentication `gh auth` has configured inside the sandbox.

## Shared Agents

### shakespeare-example

A demo agent that responds to all queries in Shakespearian prose. Useful for verifying custom agents are loading correctly in the sandbox.

### code-explainer

Explains code, architecture, and how systems work. Uses git history to surface the "why" behind code decisions — tracing back to the commit that first introduced code rather than stopping at the most recent change. Includes git health metric commands for analysing repo churn, bus factor, bug hotspots, commit velocity, and firefighting patterns.

### code-planner

Breaks down implementation ideas into structured plans following GDS Way principles. Discovers existing patterns in the codebase before prescribing solutions. Produces plans with thin vertical slices — each task has an explicit file list, test commands, commit message, and checkpoint. Plans are saved to `docs/plans/`.

### self-improve

The self-improve agent reflects on your interactions with Kiro and codifies lessons into the agent suite configuration.

#### Workflow

1. Start a sandbox session with both your work project and this repo in scope:
   ```bash
   sbx run di-kiro /path/to/your/project /path/to/ai-sandbox --kit kiro-kit
   ```

2. Do your normal work with Kiro. When you find yourself correcting Kiro's behaviour — asking it to follow a convention, use a different approach, or stop doing something — make a mental note.

3. When you're ready to capture those lessons, swap to the self-improve agent:
   ```
   /agent swap
   ```
   Select `self-improve`.

4. Optionally, describe what you noticed if the agent doesn't pick up on it from context. For example:
   - "Kiro kept using var instead of const — add that to steering"
   - "I had to remind it about our commit message format three times"
   - "It should always check for .nvmrc before running npm commands"

   If you need to explain something the agent should have inferred from the session, ask it to also improve itself so it picks up on similar patterns next time.

5. The agent will review the session context, propose a change to the shared or personal config, and wait for your approval before writing it.

#### What it can change

- **Steering files** — Add or refine coding standards and conventions
- **Agent configs** — Adjust tool permissions, prompts, or settings
- **Hooks** — Add lifecycle automation

Changes to shared config go in `kiro-kit/files/home/kiro-kit/shared/.kiro/` and affect all users. Changes to personal config go in `kiro-kit/files/home/kiro-kit/personal/.kiro/` and are gitignored.
