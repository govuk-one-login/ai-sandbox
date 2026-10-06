# ADR-001: Personal Kiro Configuration in Sandboxes

**Status:** Accepted  
**Date:** 2026-07-28  
**Deciders:** Harry Diprose

## Context

The di-kit sandbox ships shared Kiro configuration (agents, steering, prompts) bundled in the kit image. At startup, these are copied from `/home/agent/di-kit/shared/.kiro/` into `~/.kiro/`.

Users need to bring their own personal Kiro config — custom skills, steering files, hooks, knowledge bases, and agents — into the sandbox without modifying the shared kit. The personal config should overlay on top of shared config, allowing individual customisation while preserving team defaults.

The `spec.yaml` already anticipates this with a startup command that overlays from `/home/agent/di-kit/personal/.kiro/` if present — but there is currently no mechanism to get user files into that path.

## Research

### How Kiro resolves configuration

Kiro CLI reads configuration at three scopes with the following priority:

| Priority | Scope | Path |
|----------|-------|------|
| 1 (highest) | Agent | Defined in agent JSON config |
| 2 | Project | `<workspace>/.kiro/` |
| 3 (lowest) | Global | `~/.kiro/` (or `KIRO_HOME`) |

The `KIRO_HOME` environment variable redirects the global `~/.kiro` directory to a custom location. All resolution (agents, prompts, skills, steering, settings, sessions) follows `KIRO_HOME` when set.

**Key limitation:** Kiro does not support multiple global directories or merging config from several paths. There is no `KIRO_INCLUDE_PATHS` or similar.

### How Docker SBX handles agent config

`sbx skills import` copies host-side agent skills into a persistent store that is mounted into sandboxes at startup. Supported agents:

| Agent | Host source | Sandbox mount |
|-------|-------------|---------------|
| Claude Code | `~/.claude/skills` | `/home/agent/.claude/skills` |
| Codex | `~/.agents/skills` | `/home/agent/.agents/skills` |
| Copilot | `~/.copilot/skills` | `/home/agent/.copilot/skills` |
| Cursor | `~/.cursor/skills` | `/home/agent/.cursor/skills` |
| Droid | `~/.factory/skills` | `/home/agent/.factory/skills` |

**Kiro is not in this list.** There is no `~/.kiro/skills` → sandbox mapping.

### How SBX kits work

- **Sandbox kits** (`kind: sandbox`) define a full agent: image, entrypoint, network, commands.
- **Mixin kits** (`kind: mixin`) extend an existing sandbox kit with extra files, commands, network rules, and environment variables.
- Multiple kits can be stacked: `sbx run <name> . --kit <sandbox-kit> --kit <mixin1> --kit <mixin2>`
- A mixin's `files/` tree is merged into the sandbox filesystem.
- Kits can also be added to running sandboxes with `sbx kit add`.

### Current di-kit startup sequence

```yaml
startup:
  - command: ["/bin/sh", "-c", "cp -r /home/agent/di-kit/shared/.kiro/. /home/agent/.kiro/"]
    user: "1000"
    description: "Copy shared Kiro config to ~/.kiro"
  - command: ["/bin/sh", "-c", "if [ -d /home/agent/di-kit/personal/.kiro ]; then cp -r /home/agent/di-kit/personal/.kiro/. /home/agent/.kiro/; fi"]
    user: "1000"
    description: "Overlay personal Kiro config on top of shared"
```

The personal overlay path (`/home/agent/di-kit/personal/.kiro`) already exists in the startup script — it just needs content delivered into it.

## Alternatives Considered

### Option A: Convention within the workspace

Users place a `.kiro-personal/` directory in their project root. A startup command detects it and copies contents into `~/.kiro/`.

```yaml
- command: ["/bin/sh", "-c", "if [ -d /workspace/.kiro-personal ]; then cp -r /workspace/.kiro-personal/. /home/agent/.kiro/; fi"]
  user: "1000"
```

**Pros:**
- Works today with no sbx or Kiro changes
- Simple to understand

**Cons:**
- Ties personal config to each project directory
- Doesn't work across projects without symlinks or duplication
- Pollutes workspace with non-project files
- Personal config ends up in version control unless `.gitignore`d

### Option B: Personal mixin kit (CHOSEN)

Users create a personal mixin kit that delivers files into `/home/agent/di-kit/personal/.kiro/`. The existing startup script handles the overlay.

```
my-personal-kit/
├── spec.yaml          # kind: mixin
└── files/
    └── home/
        └── di-kit/
            └── personal/
                └── .kiro/
                    ├── steering/
                    ├── agents/
                    ├── hooks/
                    └── settings/
```

Run with both kits:
```bash
sbx run di-kiro . \
  --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest \
  --kit ./my-personal-kit
```

**Pros:**
- Clean separation of shared vs personal config
- Personal config lives outside project repos
- Works across any workspace
- Uses existing startup overlay logic — no changes to di-kit needed
- Can be version-controlled independently (e.g. personal dotfiles repo)
- Can be published to a registry for use across machines
- Future-proof: if sbx adds native Kiro support, migration is straightforward

**Cons:**
- Slightly more ceremony than a simple folder drop
- Users need to understand mixin kit structure (minimal — one `spec.yaml` and a `files/` tree)
- `--kit` only applies at creation time; must use `sbx kit add` for existing sandboxes

### Option C: Wait for `sbx skills import` to support Kiro

Docker could add a Kiro row to the skills import table, mounting `~/.kiro/skills` (or similar) into the sandbox automatically.

**Pros:**
- Zero-config for users once supported
- Consistent with how other agents handle it

**Cons:**
- Not available today — no timeline for support
- Even if added, `sbx skills` only covers "skills" — not steering, hooks, agents, or knowledge bases
- Out of our control

### Option D: Use `KIRO_HOME` environment variable

Set `KIRO_HOME` in the sandbox to point at the personal config path directly.

**Pros:**
- Native Kiro mechanism
- No copy/overlay script needed

**Cons:**
- `KIRO_HOME` replaces the global directory entirely — no merge with shared config
- Would require duplicating all shared config into the personal path, defeating the purpose
- Cannot layer personal on top of shared

## Decision

**Use Option B: Personal mixin kits.**

The mixin kit approach provides clean separation between shared team config and personal customisation. It works within existing sbx and Kiro capabilities, requires no changes to either tool, and leverages the overlay logic already built into the di-kit startup sequence.

Users maintain a small personal mixin kit (locally or in a registry) containing their steering, agents, hooks, and knowledge bases. This is loaded alongside the di-kit sandbox kit at sandbox creation time.

## Consequences

- The di-kit README should document how to create and use a personal mixin kit
- A template/example personal mixin kit structure should be provided
- The existing startup overlay script in `spec.yaml` remains unchanged
- If `sbx skills import` adds Kiro support in future, we can reassess — but the mixin approach will continue to work regardless
- Users who want the simplest possible setup can still use Option A (workspace convention) as an informal alternative
