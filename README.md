# ai-sandbox

Sandbox kits for GOV.UK One Login, published to GitHub Container Registry.

Each kit is a self-contained [Docker SBX kit](https://docs.docker.com/ai/sandboxes/) that configures a sandbox environment for a specific workflow.

## Available kits

| Kit | Description | Latest |
|-----|-------------|--------|
| [di-kit](./di-kit/) | Kiro sandbox for One Login developers | `ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest` |

## Using a kit

```bash
# One-time setup: allow kits from this registry
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'

# Run a kit (example: di-kit)
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest
```

Pin to a specific version for reproducibility:

```bash
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:0.1.1
```

## Personalising your sandbox

Kits in this repo provide shared team configuration. To bring your own personal Kiro config (steering, agents, hooks, knowledge bases) into a sandbox, create a **personal mixin kit** and load it alongside the team kit.

### How it works

A mixin kit (`kind: mixin`) layers on top of a sandbox kit. The `files/` tree in your mixin is merged into the sandbox filesystem, and the kit's startup script overlays your personal config on top of the shared defaults.

### Quick start

1. Copy the template to a permanent location:

   ```bash
   cp -r examples/personal-kit-template ~/kiro-personal-kit
   ```

2. Add your config files into the `.kiro/` directories:

   ```
   ~/kiro-personal-kit/
   ├── spec.yaml
   └── files/
       └── home/di-kit/personal/.kiro/
           ├── steering/       # Your steering rules
           ├── agents/         # Your custom agents
           ├── hooks/          # Your hooks
           └── settings/       # Your settings (e.g. mcp.json)
   ```

3. Load both kits when creating a sandbox:

   ```bash
   sbx run di-kiro . \
     --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest \
     --kit ~/kiro-personal-kit
   ```

Your personal config overlays on top of the shared config — matching filenames override, new files are added alongside.

See [examples/personal-kit-template/](./examples/personal-kit-template/) for the full template and detailed instructions.

### Why a mixin kit?

See [ADR-001](./docs/adrs/001-personal-kiro-config-in-sandboxes.md) for the full decision record, including alternatives considered (workspace conventions, `KIRO_HOME`, `sbx skills import`).

## Repository structure

```
.
├── di-kit/                  # Each kit lives in its own directory
│   ├── spec.yaml            # Kit specification
│   ├── .kit_version         # Semver — bump to trigger a release
│   ├── CHANGELOG.md         # Human-readable changelog (Keep a Changelog format)
│   ├── README.md            # Kit-specific docs (usage, config, agents)
│   └── files/               # Files delivered into the sandbox
├── examples/
│   └── personal-kit-template/  # Template for personal mixin kits (copy-and-own)
├── docs/
│   └── adrs/                # Architecture Decision Records
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
sbx kit validate di-kit

# Run from local directory (no publish needed)
sbx run di-kiro . --kit di-kit
```
