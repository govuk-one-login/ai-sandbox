# claude-gateway-kit

Claude Code in a Docker sandbox, using the **DI AI gateway** instead of calling Bedrock directly.

The gateway is [LiteLLM](https://docs.litellm.ai/) in front of Claude on Amazon Bedrock, EU
inference profiles only. Every developer has their own gateway key, tied to a team, so spend is
tracked per person and team and access can be switched off in seconds.

> **Status: firebreak proof of concept.** The gateway runs in the DI AI experiment account
> (`di-mobile-wallet-ai-coding-dev`) and is reachable only from GDS networks (VPN, BYOD VPN,
> ZScaler). See [govuk-one-login/mobile-ai-coding](https://github.com/govuk-one-login/mobile-ai-coding)
> `docs/plans/litellm-gateway-firebreak.md`.

## How it differs from a Bedrock kit

| | Bedrock direct (for example `di-claude`) | `claude-gateway-kit` |
|---|---|---|
| Credentials in the sandbox | AWS SSO session (device-code login inside the microVM) | **None.** Only a placeholder. |
| Where the real credential lives | Inside the sandbox (`~/.aws/sso/cache`) | Host keychain (`sbx secret set litellm`) |
| Network allow-list | Bedrock, SSO, STS, sign-in | The gateway host only |
| Spend and kill switch | AWS Budgets and CloudTrail, per account | Per person and team, in the gateway |
| Kit type | Full sandbox (own image and entrypoint) | v3 **mixin** on Docker's built-in `claude` agent |

## Quick start

1. Get a gateway key from a gateway admin. They run
   `scripts/gateway-admin create-key <you@digital.cabinet-office.gov.uk> --team <team>`.
2. Store it on your host. It never enters a sandbox:

   ```bash
   sbx secret set litellm          # paste the key when prompted
   # or, if it's already in your macOS Keychain:
   security find-generic-password -s litellm-ai-gateway -w | sbx secret set litellm
   ```

3. Allow kits from this registry (one-off):

   ```bash
   sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'
   ```

4. Run Claude Code with the gateway mixin:

   ```bash
   sbx run claude . --kit ghcr.io/govuk-one-login/ai-sandbox/claude-gateway-kit:latest
   ```

   Approve the `litellm` credential request when prompted. **Don't** bind an `anthropic`
   credential to this sandbox. If one is bound, Claude Code may sign in to claude.ai and send that
   token to the gateway instead of your gateway key.

In Claude Code, `/status` should show `Anthropic base URL: https://<gateway host>` and a model
such as `claude-sonnet-5-5`.

## Checking it works

- Inside the sandbox, `env | grep ANTHROPIC_AUTH_TOKEN` shows a placeholder, not your key.
- Your spend goes up after a prompt. A gateway admin can check with
  `scripts/gateway-admin spend --user <you>`. You may be able to check yourself with the call
  below, though this hasn't been tested yet:

  ```bash
  curl -s https://<gateway host>/key/info -H "Authorization: Bearer <your key>" | jq '.info | {spend, max_budget, expires}'
  ```

## Configuration

Kit args, set with `--kit-arg name=value`:

| Arg | Default | Purpose |
|-----|---------|---------|
| `gatewayHost` | `dd9q1qh5bfkpx.cloudfront.net` | Allow-list entry and key-injection domain |
| `gatewayUrl` | `https://dd9q1qh5bfkpx.cloudfront.net` | `ANTHROPIC_BASE_URL`. Must match `gatewayHost`. |
| `opusModel` / `sonnetModel` / `haikuModel` | `claude-opus-5-5` / `claude-sonnet-5-5` / `claude-haiku-5-5` | Gateway aliases for Claude Code's model tiers |
| `disableNonessentialTraffic` | `1` | Sets `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` |

Available gateway models: `claude-{opus,sonnet,haiku}-5-5` and `claude-opus-4-8`,
`claude-sonnet-4-6`, `claude-haiku-4-5`.

## Local development

This is a **v3 source kit**. It's built by the `docker/sandbox-kit:3` BuildKit frontend rather than
packed by `sbx kit push`.

```bash
# Validate (the frontend checks the descriptor)
docker buildx build -f claude-gateway-kit/spec.yaml claude-gateway-kit

# Run from source (sbx creates its kit builder sandbox on first use)
sbx run claude . --kit ./claude-gateway-kit
```

CI (`.github/workflows/publish-kit.yml`) detects `schemaVersion: "3"` and validates and publishes
with `docker buildx build`. v1 kits keep using `sbx kit validate` and `sbx kit push`.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| `403 Forbidden` | You're not on a GDS network |
| `401` | No `litellm` secret, the credential wasn't approved, or the key is blocked or expired |
| `422 budget_exceeded` | Your key's or team's budget is used up |
| `/status` shows claude.ai or OAuth | An `anthropic` credential is bound. Recreate the sandbox without it. |
| Blocked domain errors | Run `sbx policy log`. Only the gateway host is allowed by this mixin. |
