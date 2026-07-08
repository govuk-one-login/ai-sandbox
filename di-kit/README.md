# AWS IAM SBX Kit

## Usage

```bash
# Package the kit
sbx kit pack di-kit

# Validate the kit
sbx kit validate di-kit

# Run the kit
sbx run di-kiro . --kit di-kit

```

## Configuration

- **AWS Region**: eu-west-2
- **SSO URL**: https://uk-digital-identity.awsapps.com/start/#/
- **Network Access**:
  - `management.us-east-1.kiro.dev:443`
  - `runtime.us-east-1.kiro.dev:443`

## Kiro Config

The kit supports shared organisation config and personal overrides, both delivered to `~/.kiro/` (global Kiro config) in the sandbox.

### Shared config (committed)

Shared config lives in `di-kit/files/home/di-kit/shared/.kiro/` and is committed to the repo.

```
di-kit/files/home/di-kit/shared/.kiro/
├── agents/
│   ├── code-explainer.json
│   ├── self-improve.json
│   └── shakespeare-example.json
└── steering/
    ├── code-explainer.md
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
