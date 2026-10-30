# Changelog

All notable changes to the claude-kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-29

### Added

- Initial kit: Claude Code on AWS Bedrock for One Login users
- AWS CLI v2 install with AWS SSO device-flow login (`uk-digital-identity.awsapps.com`)
- Shared Claude Code config: global `CLAUDE.md`, `dependabot-pr-review` skill
- Personal config overlay support (gitignored) for `~/.claude` and `~/.aws`
- Network allow list for Bedrock, AWS SSO, AWS docs, and package registries
- Telemetry and non-essential traffic disabled
