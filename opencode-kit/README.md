# opencode SBX Kit

[opencode](https://opencode.ai) kit, talking to an
OpenAI-compatible endpoint with a bearer token.

## Quick start

You need `sbx` installed, the endpoint hostname (e.g. `llm.example.com`) and a
bearer token for it. Using a local llama.cpp instead? Skip to
[Use a local model](#use-a-local-model-llamacpp).

```bash
# 1. One-time: allow kits from this registry
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'

# 2. One-time: store your token in the macOS Keychain (prompts, doesn't echo)...
security add-generic-password -s opencode-kit-api-key -a "$USER" -w

#    ...and tell sbx how to read it back. It runs on your host; the sandbox
#    only ever sees a placeholder.
sbx secret set-custom \
  --host llm.example.com \
  --env OPENCODE_MODEL_API_KEY \
  --command '/usr/bin/security find-generic-password -s opencode-kit-api-key -w'

# 3. Run
sbx run di-opencode . \
  --kit ghcr.io/govuk-one-login/ai-sandbox/opencode-kit:latest \
  --kit-arg model_endpoint=llm.example.com:443
```

`model_endpoint` is `<hostname>:443`. Use the same hostname in steps 2 and 3.
Not on macOS? Pipe the token in instead
of using the Keychain: `printf '%s' "$GATEWAY_TOKEN" | sbx secret set-custom
--host llm.example.com --env OPENCODE_MODEL_API_KEY --value-stdin`.

Tip: save the argument once instead of typing it each time:

```bash
echo 'model_endpoint=llm.example.com:443' > ~/.config/opencode-kit.args
sbx run di-opencode . \
  --kit ghcr.io/govuk-one-login/ai-sandbox/opencode-kit:latest \
  --kit-args-file ~/.config/opencode-kit.args
```

opencode starts with `endpoint/claude-sonnet-5-5` selected.

### Use a local model (llama.cpp)

Run `llama-server` on your machine on port 9931, bound to `127.0.0.1` (this
is strongly advised), then point the kit at it. No token or secret is needed:

```bash
sbx run di-opencode . \
  --kit ghcr.io/govuk-one-login/ai-sandbox/opencode-kit:latest \
  --kit-arg model_endpoint=host.docker.internal:9931
```

The kit uses plain HTTP for this one address only; every other endpoint must be
`<hostname>:443` over HTTPS. `llama-server` ignores the model name, so the
default selection works. Tested with llama.cpp on `127.0.0.1:9931`.

At startup the kit also asks the endpoint for its model list (`/v1/models`) and
adds each model to `/models`, so you can pick your llama.cpp model by name.
Start `llama-server` before `sbx run`.

## Troubleshooting

- **Only the default model in `/models`**: the endpoint wasn't reachable when
  the sandbox started, so its model list wasn't added. For llama.cpp, check
  `llama-server` is listening on port 9931 (`curl localhost:9931/v1/models` on
  your host), then recreate the sandbox. The default model still works.
- **Local model not reachable**: check `sbx policy log` for blocked hosts. This
  path mirrors the junie-kit.
- **401 from the endpoint**: the secret isn't applied. Check the `--host`
  matches the hostname in `model_endpoint`, and recreate the sandbox if you added
  the secret after creating it.
- **Connection blocked**: run `sbx policy log` to see which host was denied.
- **Wrong endpoint**: a sandbox keeps the arguments it was created with.
  Create a new sandbox (`--name`) to use a different `model_endpoint`.
- **Skills missing**: skill install failures show in `sbx logs`.

## Security model

- **No AWS access in the sandbox.** There is no AWS CLI, SSO profile or AWS
  host in the allow list.
- **The token never enters the sandbox or this repo.** The sandbox only sees a
  placeholder; the sbx proxy substitutes the real token on requests to the
  endpoint host.
- **Network is deny-by-default**: the endpoint, npm and GitHub (for skills),
  plus port 9931 on your own machine (`localhost:9931`) for a local llama.cpp.
  That port is open even when you use a remote endpoint, the same as the
  junie-kit.
- **`model_endpoint` is validated** because the value opens network access. It
  must be `<hostname>:443` (HTTPS) or exactly `host.docker.internal:9931`
  (plain HTTP, llama.cpp on your machine). No wildcards, other ports, schemes or
  paths. The bearer token is only ever sent over HTTPS.
- The sandbox itself is the security boundary; opencode runs without
  additional approval policy.

## Customising

### Model

The default is `endpoint/claude-sonnet-5-5`. To add models, extend `models` in
`files/home/opencode-kit/shared/.config/opencode/opencode.json`. The key must be
the model ID your endpoint exposes (use `modelID` to map a different name).
Models the endpoint lists at `/v1/models` are added automatically at startup by
`files/home/opencode-kit/shared/discover-endpoint-models.mjs`, so you only need
to add a model there if you want it as the default.

### Personal config

Create this gitignored directory to override shared config on your machine:

```
opencode-kit/files/home/opencode-kit/personal/
└── .config/opencode/        # e.g. your own opencode.json, AGENTS.md
```

Never put a token in personal config; use `sbx secret`.

### Agent skills

Skills aren't committed to this kit. At startup, Agent Manager installs the ones
listed in `files/home/opencode-kit/shared/ai-skills.yml` from
[govuk-one-login/agent-skills](https://github.com/govuk-one-login/agent-skills).
Edit the `skills:` list to change them.

## Local development

```bash
# End-to-end test: a real sandbox from this kit, answered by a mock OpenAI
# endpoint on port 9931. Needs sbx signed in and the Imposter CLI installed
# (`imposter`); stop llama.cpp (or anything else on 9931) first.
# See tests/e2e/opencode-kit.sh.
tests/e2e/opencode-kit.sh

# Validate (CI runs the same check; the argument is required)
sbx kit validate --offline opencode-kit --kit-arg model_endpoint=llm.example.com:443

# Run from the local directory
sbx run di-opencode . --kit opencode-kit --kit-arg model_endpoint=llm.example.com:443
```

## Releasing

1. Bump `opencode-kit/.kit_version`
2. Update `opencode-kit/CHANGELOG.md`
3. Merge to main — CI publishes `ghcr.io/govuk-one-login/ai-sandbox/opencode-kit:<version>` and `:latest`

CI validates the kit using the dummy argument in
`.github/kit-args/opencode-kit.args`. Update it if you add required arguments.

## End-to-end test

`tests/e2e/opencode-kit.sh` builds a real sandbox from this kit and checks it
against a mock OpenAI endpoint on port 9931 (the Imposter OpenAI example,
vendored in `tests/mock-openai`). It checks startup and skills, model
discovery, prompts answered through the kit's own entrypoint, and the network
allow list.

It needs `sbx` signed in, `jq` and the Imposter CLI (`brew install
imposter-project/imposter/imposter`), and fails if any is missing. Port 9931
must be free, so stop llama.cpp first.

```bash
tests/e2e/opencode-kit.sh
```

It runs locally only for now. A CI workflow,
`.github/workflows/e2e-opencode-kit.yml`, is in place, but its automatic
triggers are disabled until it has a Docker sign-in secret and has been proven
on a runner. The mock ignores `Authorization` and only the local plain-HTTP
path is covered, so it does not test a remote HTTPS endpoint or token
injection.
