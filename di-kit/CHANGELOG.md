# Changelog

All notable changes to the di-kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-23

### Added

- New dependabot folder to seporate agent needs
- Opening up dependabot to allow for NPM install of dependencies and copying of CI pipeline error logs

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

