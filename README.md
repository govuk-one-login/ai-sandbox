# ai-sandbox

Sandbox kits for GOV.UK One Login, published to GitHub Container Registry.

Each kit is a self-contained [Docker SBX kit](https://docs.docker.com/ai/sandboxes/) that configures a sandbox environment for a specific workflow.

## Available kits

| Kit | Description | Latest |
|-----|-------------|--------|
| [kiro-kit](./kiro-kit/) | Kiro sandbox for One Login developers | `ghcr.io/govuk-one-login/ai-sandbox/kiro-kit:latest` |
| [claude-kit](./claude-kit/) | Claude Code on AWS Bedrock sandbox for One Login developers | `ghcr.io/govuk-one-login/ai-sandbox/claude-kit:latest` |

## Using a kit

```bash
# One-time setup: allow kits from this registry
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'

# Run a kit (example: kiro-kit)
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/kiro-kit:latest
```

Pin to a specific version for reproducibility:

```bash
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/kiro-kit:0.1.1
```

## Shared agent skills

Skills (such as `incremental-commits`) don't live in this repo. Their canonical home
is [govuk-one-login/agent-skills](https://github.com/govuk-one-login/agent-skills);
kits install the skills they need at sandbox startup with
[Agent Manager](https://github.com/ai-agent-manager/agent-manager), pulling each skill
from the source repositories declared in the agent-skills discovery document.

To install shared skills into a coding assistant on the host (e.g. Kiro or Claude Code
running on your Mac against this repo):

```bash
npx -y @ai-agent-manager/cli@latest govuk-one-login/agent-skills
```

The interactive menu lists all available skills and asks where to install them.
Skills installed into a repo (`.kiro/skills/`, `.claude/skills/`) are gitignored here.

## Repository structure

```
.
├── kiro-kit/                  # Each kit lives in its own directory
│   ├── spec.yaml            # Kit specification
│   ├── .kit_version         # Semver — bump to trigger a release
│   ├── CHANGELOG.md         # Human-readable changelog (Keep a Changelog format)
│   ├── README.md            # Kit-specific docs (usage, config, agents)
│   └── files/               # Files delivered into the sandbox
└── .github/workflows/
    └── publish-kit.yml      # CI: validate on PR, publish on merge when version changes
```

## Contributing

### Adding or modifying a kit

1. Make your changes in the kit's directory
2. Open a PR — CI will validate the kit structure
3. Merge to main

If your change doesn't require a new release (e.g. updating docs), just merge. The publish step only runs when `.kit_version` has been bumped to a version that hasn't been tagged yet.

### Releasing a new version

1. Bump the version in `<kit>/.kit_version` (semver: `MAJOR.MINOR.PATCH`)
2. Update `<kit>/CHANGELOG.md` with what changed
3. Merge to main

CI will automatically:
- Validate the kit
- Push to `ghcr.io/govuk-one-login/ai-sandbox/<kit>:<version>` and `:latest`
- Tag the commit as `<kit>/v<version>`
- Create a GitHub Release with auto-generated notes

### Local development

```bash
# Validate a kit
sbx kit validate kiro-kit

# Run from local directory (no publish needed)
sbx run di-kiro . --kit kiro-kit
```
