# One Login — team conventions

<!--
Global memory for Claude Code in the di-claude sandbox.
Applies to every workspace in the sandbox. Keep it short —
every token competes with the conversation for context.
-->

## Environment

- GOV.UK One Login (Digital Identity) services.
- AWS region: eu-west-2. Claude models are served via AWS Bedrock.

## Conventions

- Keep changes small and reviewable; one logical change per commit.
- Commit messages: imperative mood, reference the work item where applicable.
- Prefer editing existing code over adding new abstractions.
- When unsure about a team-specific convention, ask rather than guess.

## Testing

- Run the project's own test commands before considering work done.
- Name the specific check that verifies the change, not "ran the tests".
