# Vendored: Imposter OpenAI mock

Modified copy of the OpenAI-compatible mock from the Imposter examples.

- Source: https://github.com/imposter-project/examples/tree/63f62902e1d7e5e3e1f8f3e26d4cb2c0c2c68fb2/rest/openai
- Commit: `63f62902e1d7e5e3e1f8f3e26d4cb2c0c2c68fb2`
- Licence: Apache-2.0 (`LICENSE`, copied from the same commit)
- Vendored: `openai-config.yaml` and `responses/*`. The upstream `harness/` (a
  Python SDK smoke test) and `README.md` are not included.
- Added by this repo (not upstream): `imposter-project.yaml`, which tells the
  Imposter CLI to use the native engine at a pinned version.

Used by `tests/e2e/opencode-kit.sh` as the model endpoint on port 9931, started
with the Imposter CLI (`imposter up`). Do not edit the vendored files: to
update, re-copy from a newer upstream commit and change the commit above.

Behaviour to know about:
- With the standalone `imposter-go` engine the requested `model` is not echoed
  into responses (they report `gpt-4o`), so the test does not assert on it.
- Chat replies are canned. The plain and streamed replies start with
  `Hello from Imposter!`, which is what the test looks for.
