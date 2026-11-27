# Changelog

All notable changes to the opencode-kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-24

### Added

- Initial release: run opencode in a sandbox against an
  OpenAI-compatible endpoint. Pass the endpoint with
  `--kit-arg model_endpoint=<host>:443`, and store your bearer token once with
  `sbx secret set-custom` so the sandbox never sees the real token.
- opencode 1.19.5 starts with the endpoint set up and `claude-sonnet-5-5`
  selected. To use llama.cpp on your machine instead, pass
  `--kit-arg model_endpoint=host.docker.internal:9931`.
- The models your endpoint offers are listed in `/models` automatically.
- The sandbox has no AWS access and can reach only your endpoint, npm, GitHub
  and port 9931 on your machine (for llama.cpp).
- Team skills (`incremental-commits`, `typescript-development`) are installed
  automatically at startup.
- Add your own opencode settings in a gitignored `personal/` directory.
