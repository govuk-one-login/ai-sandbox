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
└── agents/
    └── shakespeare-example.json    # example custom agent
```

### Personal config (not committed)

Personal config lives in `di-kit/files/home/di-kit/personal/.kiro/` and overrides shared config. This directory is gitignored — create it manually and add your own config.

### How it works

1. The kit's `files/home/` mechanism delivers `di-kit/shared/` and `di-kit/personal/` (if it exists) to `/home/agent/di-kit/` in the container
2. A startup command copies `/home/agent/di-kit/shared/.kiro/` into `~/.kiro/`
3. A second startup command copies `/home/agent/di-kit/personal/.kiro/` over `~/.kiro/`

Shared is applied first, then personal overlays on top. This uses Kiro's global steering — config in `~/.kiro/` applies to all workspaces in the sandbox.

### Included examples

- **Agent** (`shakespeare-example.json`): A demo agent that responds in Shakespearian prose

### Switching agents in the sandbox

Once inside the sandbox, switch to a custom agent with:

```
/agent swap
```

Then select `shakespeare-example` from the list.
