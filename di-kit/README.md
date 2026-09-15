# AWS IAM SBX Kit

## Quick start

```bash
# One-time setup: allow kits from ghcr.io/govuk-one-login
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/govuk-one-login/"]'

# Run the sandbox with the latest published kit
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest
```

To pin to a specific version:

```bash
sbx run di-kiro . --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:1.0.0
```

## Local development

When iterating on the kit itself, use the local path:

```bash
# Validate the kit
sbx kit validate di-kit

# Run from local directory
sbx run di-kiro . --kit di-kit
```

## Releasing

1. Bump the version in `di-kit/.kit_version`
2. Update `di-kit/CHANGELOG.md` with what changed
3. Merge to main — CI publishes automatically

CI will:
- Validate the kit
- Push `ghcr.io/govuk-one-login/ai-sandbox/di-kit:<version>` and `:latest`
- Tag the commit as `di-kit/v<version>`
- Create a GitHub Release with auto-generated notes

The publish only fires when `.kit_version` contains a version that hasn't been tagged yet, so merging doc-only changes won't trigger a release.

A manual **workflow_dispatch** trigger is available as a fallback if needed (Actions → Publish di-kit → Run workflow on `main`).

## Configuration

- **AWS Region**: eu-west-2
- **SSO URL**: https://uk-digital-identity.awsapps.com/start/#/
- **Network Access**:
  - `management.us-east-1.kiro.dev:443`
  - `runtime.us-east-1.kiro.dev:443`

## Network egress monitoring

The kit records the outbound network traffic that Kiro and its tools make
from inside the sandbox. This gives visibility into where the agent is
connecting, without relying on the paid AI Governance add-on.

Monitoring (the in-guest proxy) is **enabled by default**. Disable it for a
run by setting `DISABLE_MONITOR_EGRESS`:

```bash
sbx run di-kiro . --kit di-kit -e DISABLE_MONITOR_EGRESS=1 --name di-kiro
```

The flag is baked into the sandbox at creation and reapplied on re-attach
(accepted "off" values: unset/empty, `0`, `false`, `no`). The host-side
`tools/watch-egress.py` is unaffected — it reads sbx's own policy log, so it
works regardless of this setting.

### How it works

- A small, dependency-free logging forward proxy is delivered to the sandbox
  at `~/di-kit/monitoring/egress-proxy.py` (source:
  `di-kit/files/home/di-kit/monitoring/egress-proxy.py`).
- The sandbox entrypoint starts the proxy, waits for it to become ready, and
  then points the standard `HTTP_PROXY` / `HTTPS_PROXY` variables at it so all
  well-behaved clients route through it.
- The proxy **chains to the proxy sbx already configures** (its host-side
  forward proxy) via `EGRESS_UPSTREAM_PROXY`, so traffic is observed without
  bypassing the sandbox's own egress controls.
- HTTPS is logged at the `CONNECT` level only — target host, port and bytes
  transferred, with outcome `opened`. Payloads are **not** decrypted (no TLS
  interception, no CA injection). Plain HTTP requests additionally log the
  method, URL and response status.

> **Which component tells me if a request was blocked?** sbx intercepts TLS
> and enforces a deny *inside* the encrypted session, so the in-guest proxy
> can only see that an HTTPS tunnel *opened* — it cannot tell allowed from
> blocked. For the authoritative verdict use `tools/watch-egress.py` (below);
> the in-guest proxy is for per-connection **detail** (hosts, byte volumes,
> timing, plain-HTTP URLs).

### Blocked vs allowed (authoritative)

`tools/watch-egress.py` runs on the **host** and streams a live allowed/blocked
feed from `sbx policy log --json`. This is the reliable verdict source and
needs no paid licence.

```bash
tools/watch-egress.py di-kiro          # live feed for one sandbox
tools/watch-egress.py                  # all sandboxes (tags each with [vm])
tools/watch-egress.py di-kiro --once   # one-shot snapshot
tools/watch-egress.py di-kiro -i 1     # 1s poll interval
```

Example output:

```
· 2026-09-08 15:18:54  ALLOW  pypi.org:443                    forward-bypass  x1
· 2026-09-09 11:05:30  BLOCK  www.google.com:443              No matching allow rule (default deny)  x4
```

The underlying command is `sbx policy log di-kiro` (add `--json` for the raw
structured form the watcher parses).

### Per-connection detail (in-guest proxy)

- Structured events: `~/di-kit/monitoring/logs/egress.jsonl` (one JSON object
  per line).
- Proxy stdout/stderr: `~/di-kit/monitoring/logs/proxy.out`.

Each event looks like:

```json
{"ts":"2026-09-03T10:15:23Z","session_id":"…","event":"connect",
 "outcome":"opened","host":"kiro.dev","port":443,"via":"parent",
 "status":200,"bytes_out":517,"bytes_in":8213,"duration_ms":142}
```

Key fields:

- `event` — `connect` (HTTPS/TLS tunnel), `http` (plain HTTP), or a
  `proxy_start` / `proxy_stop` lifecycle event.
- `outcome` — for `connect`: `opened` (tunnel established; verdict per sbx) or
  `error` (upstream unreachable). For `http`: `allowed`, `blocked` (upstream
  returned `403`/`407`), or `error`. **Note:** HTTPS is never `blocked` here —
  ask `watch-egress.py` for that.
- `status` / `reason` — status code and reason phrase from the upstream proxy.
- `via` — `parent` when chained through sbx's proxy, else `direct`.
- `bytes_out` / `bytes_in` / `duration_ms` — volume and timing.

Tail the raw stream inside the sandbox (replace `di-kiro` with your sandbox
name):

```bash
sbx exec -it di-kiro sh -c 'tail -f -n +1 ~/di-kit/monitoring/logs/egress.jsonl'
```

For a compact, human-readable feed:

```bash
sbx exec -it di-kiro python3 -u -c '
import json, subprocess
p = subprocess.Popen(
    ["tail","-f","-n","+1","/home/agent/di-kit/monitoring/logs/egress.jsonl"],
    stdout=subprocess.PIPE, text=True)
for line in p.stdout:
    try: e = json.loads(line)
    except Exception: continue
    if e.get("event") in ("connect","http"):
        print(f"{e[\"ts\"][11:19]}  {e.get(\"outcome\",\"?\"):7} "
              f"{e.get(\"method\",\"CONNECT\"):7} "
              f"{e[\"host\"]}:{e[\"port\"]:<5} {e.get(\"status\",\"\")} "
              f"{e.get(\"reason\",\"\")}")'
```

### Configuration

The proxy reads these environment variables (all optional):

| Variable | Default | Purpose |
|----------|---------|---------|
| `EGRESS_PROXY_PORT` | `8080` | Listen port inside the sandbox |
| `EGRESS_LOG_FILE` | `~/di-kit/monitoring/logs/egress.jsonl` | JSONL output path |
| `EGRESS_UPSTREAM_PROXY` | (sbx's proxy) | Parent proxy to chain through |

### Limitations and extending

- Only captures clients that honour `HTTP_PROXY` / `HTTPS_PROXY`. sbx still
  enforces its own egress policy for everything else.
- The in-guest proxy cannot determine allowed/blocked for HTTPS (sbx enforces
  inside intercepted TLS). Use `tools/watch-egress.py` for the verdict.
- Metadata only — no request/response bodies are recorded.
- The proxy is a self-contained script with a single `log_event()` sink, so it
  is straightforward to extend later (for example, forwarding events to an
  OpenTelemetry collector) without changing how traffic is routed.

## Kiro Config

The kit supports shared organisation config and personal overrides, both delivered to `~/.kiro/` (global Kiro config) in the sandbox.

### Shared config (committed)

Shared config lives in `di-kit/files/home/di-kit/shared/.kiro/` and is committed to the repo.

```
di-kit/files/home/di-kit/shared/.kiro/
├── agents/
│   ├── code-explainer.json
│   ├── code-planner.json
│   ├── self-improve.json
│   └── shakespeare-example.json
└── steering/
    ├── code-explainer.md
    ├── code-planner.md
    └── self-improve-prompt.md
```

### Personal config (not committed)

Personal config lives in `di-kit/files/home/di-kit/personal/.kiro/` and overrides shared config. This directory is gitignored — create it manually and add your own config.

### How it works

1. The kit's `files/home/` mechanism delivers `di-kit/shared/` and `di-kit/personal/` (if it exists) to `/home/agent/di-kit/` in the container
2. A startup command copies `/home/agent/di-kit/shared/.kiro/` into `~/.kiro/`
3. A second startup command copies `/home/agent/di-kit/personal/.kiro/` over `~/.kiro/`

Shared is applied first, then personal overlays on top. This uses Kiro's global steering — config in `~/.kiro/` applies to all workspaces in the sandbox.

### Included agents

- **code-explainer** — Explains code and architecture using git history
- **code-planner** — Creates structured implementation plans
- **self-improve** — Reflects on feedback and improves the agent suite
- **shakespeare-example** — Demo agent responding in Shakespearian prose

### Switching agents in the sandbox

Once inside the sandbox, switch to a custom agent with:

```
/agent swap
```

Then select an agent from the list.

## Shared Agents

### shakespeare-example

A demo agent that responds to all queries in Shakespearian prose. Useful for verifying custom agents are loading correctly in the sandbox.

### code-explainer

Explains code, architecture, and how systems work. Uses git history to surface the "why" behind code decisions — tracing back to the commit that first introduced code rather than stopping at the most recent change. Includes git health metric commands for analysing repo churn, bus factor, bug hotspots, commit velocity, and firefighting patterns.

### code-planner

Breaks down implementation ideas into structured plans following GDS Way principles. Discovers existing patterns in the codebase before prescribing solutions. Produces plans with thin vertical slices — each task has an explicit file list, test commands, commit message, and checkpoint. Plans are saved to `docs/plans/`.

### self-improve

The self-improve agent reflects on your interactions with Kiro and codifies lessons into the agent suite configuration.

#### Workflow

1. Start a sandbox session with both your work project and this repo in scope:
   ```bash
   sbx run di-kiro /path/to/your/project /path/to/ai-sandbox --kit di-kit
   ```

2. Do your normal work with Kiro. When you find yourself correcting Kiro's behaviour — asking it to follow a convention, use a different approach, or stop doing something — make a mental note.

3. When you're ready to capture those lessons, swap to the self-improve agent:
   ```
   /agent swap
   ```
   Select `self-improve`.

4. Optionally, describe what you noticed if the agent doesn't pick up on it from context. For example:
   - "Kiro kept using var instead of const — add that to steering"
   - "I had to remind it about our commit message format three times"
   - "It should always check for .nvmrc before running npm commands"

   If you need to explain something the agent should have inferred from the session, ask it to also improve itself so it picks up on similar patterns next time.

5. The agent will review the session context, propose a change to the shared or personal config, and wait for your approval before writing it.

#### What it can change

- **Steering files** — Add or refine coding standards and conventions
- **Agent configs** — Adjust tool permissions, prompts, or settings
- **Hooks** — Add lifecycle automation

Changes to shared config go in `di-kit/files/home/di-kit/shared/.kiro/` and affect all users. Changes to personal config go in `di-kit/files/home/di-kit/personal/.kiro/` and are gitignored.
