# Personal Kiro Kit Template

This is a template for creating your own personal mixin kit to bring custom Kiro configuration into the di-kit sandbox.

## What this does

When loaded alongside di-kit, this mixin delivers your personal Kiro config into the sandbox. The di-kit startup script overlays it on top of the shared team config, so your customisations take priority without replacing team defaults.

## Setup

1. Copy this template to a permanent location on your machine:

   ```bash
   cp -r examples/personal-kit-template ~/kiro-personal-kit
   ```

2. Add your config files into the `.kiro/` directories:

   ```
   ~/kiro-personal-kit/
   ├── spec.yaml
   ├── README.md
   └── files/
       └── home/di-kit/personal/.kiro/
           ├── steering/       # Your steering rules (.md files)
           ├── agents/         # Your custom agents (.json files)
           ├── hooks/          # Your hooks
           └── settings/       # Your settings (e.g. mcp.json)
   ```

3. Remove the `.gitkeep` files once you've added real content.

## Usage

Load your personal kit alongside di-kit when creating a sandbox:

```bash
sbx run di-kiro . \
  --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest \
  --kit ~/kiro-personal-kit
```

Or add it to an existing sandbox:

```bash
sbx kit add <sandbox-name> ~/kiro-personal-kit
```

## How it works

The di-kit sandbox has two startup steps:

1. Copy shared team config from `/home/agent/di-kit/shared/.kiro/` → `~/.kiro/`
2. If `/home/agent/di-kit/personal/.kiro/` exists, overlay it on top

This mixin delivers your files into that `personal/` path. Matching filenames override the shared version; new files are added alongside.

## Tips

- **Version control it.** Keep your personal kit in a dotfiles repo or similar — it's just a directory with a `spec.yaml` and a `files/` tree.
- **Keep it light.** Only add files that differ from or extend the shared config. You don't need to duplicate team defaults.
- **Steering files** are merged by Kiro at the directory level — your personal steering files sit alongside the shared ones, they don't replace the directory.
- **Agents** with the same filename as a shared agent will override it. Use unique names to add new agents without conflict.
- **`--kit` only applies at creation time.** If you update your personal kit, either recreate the sandbox or use `sbx kit add` to apply changes.

## Optional: publish to a registry

If you use multiple machines, you can publish your personal kit:

```bash
sbx kit push ~/kiro-personal-kit ghcr.io/<your-username>/kiro-personal-kit:latest
```

Then use it from anywhere:

```bash
sbx run di-kiro . \
  --kit ghcr.io/govuk-one-login/ai-sandbox/di-kit:latest \
  --kit ghcr.io/<your-username>/kiro-personal-kit:latest
```
