# Changelog

Repository-level changes to the AI sandbox kits. Changes to an individual kit
are recorded in that kit's own `CHANGELOG.md`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- [opencode-kit](./opencode-kit/CHANGELOG.md): opencode sandbox for an
  OpenAI-compatible endpoint, including a local llama.cpp.
- `tests/e2e/opencode-kit.sh`: end-to-end test that builds a real sandbox from
  opencode-kit and drives it against a vendored Imposter OpenAI mock
  (`tests/mock-openai`). Runs locally. Its CI workflow
  (`e2e-opencode-kit.yml`) has automatic triggers disabled until it has a
  Docker sign-in secret.

### Changed

- Kit validation in CI (`validate-kits.yml`, `publish-kit.yml`) now passes
  `.github/kit-args/<kit>.args` when it exists, so kits that declare required
  arguments can be validated offline.
