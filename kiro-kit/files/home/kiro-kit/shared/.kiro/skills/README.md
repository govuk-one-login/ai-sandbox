# Skills

Skills shipped with the di-kit.
See [docs/skills.md](../../docs/skills.md) for conventions on writing new skills.

## Available skills

| Skill | Description | Version |
|-------|-------------|---------|
| [dependabot-pr-review](./dependabot-pr-review/) | Review and triage Dependabot PRs — single or batch | 1.0.0 |

## Required permissions

Each skill needs specific access to function.
Follow the principle of least privilege: grant only the permissions listed, scoped as tightly as possible.

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

## Setting up secrets with sbx

The sandbox proxy authenticates API requests on behalf of the agent — the token is never exposed directly inside the sandbox.

### 1. Create a fine-grained PAT

1. Go to [GitHub → Settings → Developer settings → Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Set **Resource owner** to the org or account that owns the repos
3. Under **Repository access**, select only the repos you want to review
4. Under **Permissions**, grant the permissions from the table above
5. Generate and copy the token

### 2. Store the token with sbx

```bash
# Global — available to all sandboxes on this machine
sbx secret set -g github

# Or scoped to a specific sandbox
sbx secret set <sandbox-name> github
```

You'll be prompted to paste the token.
Alternatively, pipe it from a secret manager:

```bash
gh auth token | sbx secret set -g github
```

### 3. Verify

```bash
sbx secret ls
```

You should see `github` listed with the appropriate scope (global or sandbox-specific).

### How it works at runtime

When the sandbox starts, the sbx proxy intercepts requests to `api.github.com` and attaches the stored token automatically.
The skill's API-first approach (`curl` to `api.github.com`) works without any `Authorization` header in the commands — the proxy handles it transparently.

If no GitHub secret is configured, the skill falls back to the `gh` CLI command set, which uses whatever authentication `gh auth` has configured inside the sandbox.
