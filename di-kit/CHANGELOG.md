# Changelog

All notable changes to the di-kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-09-02

### Added

- Network egress monitoring: a self-contained, stdlib-only logging forward
  proxy (`files/home/di-kit/monitoring/egress-proxy.py`) is started by the
  entrypoint and records every outbound connection (host, port, bytes and
  timing) as JSON lines to `~/di-kit/monitoring/logs/egress.jsonl`. Tools are
  routed through it via `HTTP_PROXY`/`HTTPS_PROXY`, and it chains to the
  sandbox's existing upstream proxy so egress is observed without bypassing
  sbx. HTTPS is logged at the CONNECT level only (no TLS interception) with
  outcome `opened`; plain HTTP records `allowed`/`blocked`/`error`. See the
  "Network egress monitoring" section in `README.md`.
- `tools/watch-egress.py`: host-side live monitor that streams the
  authoritative allowed/blocked egress verdict from `sbx policy log --json`
  (no paid licence required). This is the reliable "was it blocked?" view,
  since sbx enforces HTTPS denies inside intercepted TLS that the in-guest
  proxy cannot read.
- Egress monitoring (the in-guest proxy) is enabled by default and can be
  disabled per run with `DISABLE_MONITOR_EGRESS` (e.g.
  `sbx run di-kiro . --kit di-kit -e DISABLE_MONITOR_EGRESS=1`).
- Skills conventions documentation (`docs/skills.md`)
- Skills README with index, required permissions, and `sbx secret` setup guide
- First skill: `dependabot-pr-review` (v1.0.0) — review and triage Dependabot PRs for One Login repos (Gradle, Maven, SPM, npm)

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

