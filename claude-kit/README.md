# Claude Code SBX Kit

Claude Code running on AWS Bedrock, configured for One Login users.

## Quick start

```bash
# One-time setup: allow kits from ghcr.io/govuk-one-login
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'

# Run the sandbox with the latest published kit
sbx run ghcr.io/govuk-one-login/ai-sandbox/claude-kit:latest .
```

To pin to a specific version:

```bash
sbx run ghcr.io/govuk-one-login/ai-sandbox/claude-kit:0.1.0 .
```

## Local development

When iterating on the kit itself, use the local path:

```bash
# Validate the kit
sbx kit validate claude-kit

# Run from local directory
sbx run ./claude-kit .
```

## First-time setup (required)

The shared AWS profile in `files/home/claude-kit/shared/.aws/config` ships with
placeholders. Before the kit is useful to others, replace:

- `sso_account_id` — the AWS account for your IAM Identity Center role
- `sso_role_name` — the role name to assume
- `sso_region` — confirm it matches the `device.sso.*` / `portal.sso.*`
  hosts in the `spec.yaml` network allow list (adjust both if it differs)

On first run the entrypoint starts an **AWS SSO device flow**: a code and URL
appear in the terminal, you complete sign-in in your browser, and Claude Code
launches. Subsequent starts skip login while credentials are valid; when they
expire, Claude Code re-runs the device flow automatically via `awsAuthRefresh`.

## How it works

1. The kit installs AWS CLI v2 (the `aws sso login` device-flow command is
   v2-only; `pip install awscli` pulls v1, which doesn't have it).
2. The entrypoint checks `aws sts get-caller-identity --profile di` and, if
   credentials are missing or expired, runs `aws sso login --no-browser
   --use-device-code`, then `exec claude`.
3. Startup commands copy shared config into the agent's home:
   - `shared/.claude/` → `~/.claude/` (global memory, skills)
   - `shared/.aws/` → `~/.aws/` (SSO profile)
   - `personal/` overlays on top of both, if present
4. `CLAUDE_CODE_USE_BEDROCK=1` plus `AWS_REGION` and `AWS_PROFILE` route
   Claude Code through Bedrock using the AWS SDK credential chain.

## Configuration

- **Bedrock region**: eu-west-2 (`AWS_REGION`)
- **SSO URL**: https://uk-digital-identity.awsapps.com/start/#/
- **AWS profile**: `di`

### Pinning models

No model is pinned by default — Claude Code uses its current Bedrock defaults.
To pin, add variables to the `environment.variables` block in `spec.yaml`,
for example:

```yaml
ANTHROPIC_MODEL: "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
```

The `eu.` prefix requests EU data residency; use the prefix that matches your
residency requirements. Inside a running sandbox you can also use
`/setup-bedrock` to change pins interactively (it writes to
`~/.claude/settings.json`, which is ephemeral — mirror the result into
`spec.yaml` to make it durable).

### Permission mode

The entrypoint launches Claude Code with `--dangerously-skip-permissions`,
matching Docker's built-in `claude` agent: the sandbox microVM is the security
boundary, so in-sandbox permission prompts are dropped. Remove the flag from
`spec.yaml` if you want Claude Code's own approval prompts.

## Kiro-style config layout

Shared config lives in `claude-kit/files/home/claude-kit/shared/` and is
committed to the repo:

```
claude-kit/files/home/claude-kit/shared/
├── claude-settings.json     # passed via --settings (not copied into ~/.claude/)
└── .claude/
    ├── CLAUDE.md            # global memory / team conventions
    └── skills/
        └── dependabot-pr-review/
            └── SKILL.md
```

`claude-settings.json` is deliberately kept out of `~/.claude/`: sbx reserves
`~/.claude/settings.json` for its own setup and would clobber a copied file.
The `--settings` flag is the supported way to supply an additional settings
file.

Personal config lives in `claude-kit/files/home/claude-kit/personal/` and
overrides shared config. This directory is gitignored — create it manually:

```
claude-kit/files/home/claude-kit/personal/
├── .claude/     # e.g. your own skills, agents, CLAUDE.md additions
└── .aws/        # e.g. a personal AWS profile
```

## Releasing

1. Bump the version in `claude-kit/.kit_version`
2. Update `claude-kit/CHANGELOG.md` with what changed
3. Merge to main — CI publishes automatically

CI will:
- Validate the kit
- Push `ghcr.io/govuk-one-login/ai-sandbox/claude-kit:<version>` and `:latest`
- Tag the commit as `claude-kit/v<version>`
- Create a GitHub Release with auto-generated notes

The publish only fires when `.kit_version` contains a version that hasn't been
tagged yet, so merging doc-only changes won't trigger a release.
