# Changelog

All notable changes to the One Login Kits will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-11-03

### Breaking

- rename di-kit -> kiro-kit

### Added

- Skills conventions documentation (`docs/skills.md`)
- `dependabot-pr-review` skill (v1.0.0), installed at sandbox startup from
  [govuk-one-login/agent-skills](https://github.com/govuk-one-login/agent-skills)
  via [Agent Manager](https://github.com/ai-agent-manager/agent-manager) —
  skill set declared in `files/home/kiro-kit/shared/ai-skills.yml`
- Kiro hardening config: `etc/kiro/managed-settings.json` and
  `.kiro/settings/` (`.kiroignore`, `permissions.yaml`)
- GitHub API hosts to the network allow list (required for skill installs)

### Changed

- Agent skills are no longer committed to the kit — the single canonical copy
  lives in the agent-skills repo and is installed at startup
- Required permissions and `sbx secret` setup for skills moved from the
  removed `skills/README.md` into the kit README
- README and self-improve prompt updated for the kiro-kit paths

### Fixed

- Startup config copy paths still pointed at `/home/agent/di-kit/` after the
  rename, so shared config was not being copied

## [0.1.2] - 2026-10-01

### Changed

  - Updated kit network allow list to use Kiro eu-central-1 regions rather than us-east-1 because the Kiro instance was migrated

## [0.1.1] - 2026-07-016

### Added

- NPM to the allowlist to grant access to needed dependencies
- Folder .idea/ to .gitignore

## [0.1.0] - 2026-07-09

### Added

- Initial kit with Kiro sandbox configuration
- Shared Kiro agents: code-explainer, code-planner, self-improve, shakespeare-example
- Personal config overlay support (gitignored)
- AWS IAM Identity Center SSO integration
- Network allowlist for Kiro, AWS, and PyPI endpoints
- CI workflow to validate and publish kit to ghcr.io

