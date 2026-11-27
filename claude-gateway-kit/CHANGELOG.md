# Changelog

All notable changes to claude-gateway-kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-27

### Added

- v3 mixin for Docker's built-in `claude` agent that routes Claude Code through the DI AI gateway
  (LiteLLM, Claude on Bedrock EU inference profiles)
- Per-developer gateway key from the host secret `litellm`, injected by the sbx proxy as
  `Authorization: Bearer` on the gateway host only. The sandbox sees a placeholder.
- Network allow-list limited to the gateway host
- Kit args for the gateway URL and the Opus, Sonnet and Haiku aliases (defaults: the 5.5 models)
