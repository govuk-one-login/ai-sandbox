# Changelog

All notable changes to the claude-kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-29

### Added

- Initial kit: Claude Code on AWS Bedrock for One Login users
- AWS CLI v2 install with AWS SSO device-flow login (`uk-digital-identity.awsapps.com`)
- Shared Claude Code config: global `CLAUDE.md`
- Agent skills installed at sandbox startup from
  [govuk-one-login/agent-skills](https://github.com/govuk-one-login/agent-skills)
  via [Agent Manager](https://github.com/ai-agent-manager/agent-manager)
  (skill set configured in `files/home/claude-kit/shared/ai-skills.yml`,
  initially `dependabot-pr-review`)
- Personal config overlay support (gitignored) for `~/.claude` and `~/.aws`
- Network allow list for Bedrock, AWS SSO, AWS docs, package registries,
  and GitHub (skill installs)
- Telemetry and non-essential traffic disabled
