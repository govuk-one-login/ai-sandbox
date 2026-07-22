# Rulesets

This directory contains JSON rulesets for the `ai-sandbox` GitHub repo. For convenience there is some duplication with the GitHub docs in this file. For more on rulesets see the [ruleset docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets) and the [rule API spec](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28).

## Managing rulesets

All rulesets on the repo should be defined in JSON here, except those set externally (e.g. organisation-level security rules). We manage rulesets using the GitHub API — to use the API you'll need a GitHub fine-grained personal access token (PAT) with the following permissions on the `govuk-one-login/ai-sandbox` repo:

- Read access to metadata
- Read and Write access to administration

All HTTP calls below are represented using `curl`, and values that need to be filled in are wrapped in double curly braces: `{{ }}`.

### Workflow

To update or create a ruleset you should:

1. Update or create the JSON for the ruleset
2. Commit to a branch and open a PR in GitHub
3. Merge to `main` after approval as usual
4. Optionally, if you're updating a ruleset retrieve it from GitHub before making any changes
5. Use the API calls detailed below to apply the change
6. Optionally, if you retrieved the ruleset before, retrieve it again and diff the two JSON objects
7. Alternatively, use the GitHub UI to inspect the ruleset and verify your changes

### Retrieving a ruleset

```bash
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer {{ GitHub PAT }}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/govuk-one-login/ai-sandbox/rulesets/{{ ruleset ID }}
```

### Updating a ruleset

```bash
curl -L \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer {{ GitHub PAT }}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/govuk-one-login/ai-sandbox/rulesets/{{ ruleset ID }} \
  -d @.github/rulesets/{{ ruleset file name }}
```

### Creating a ruleset

```bash
curl -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer {{ GitHub PAT }}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/govuk-one-login/ai-sandbox/rulesets \
  -d @.github/rulesets/{{ ruleset file name }}
```

## Current rulesets

| File | Ruleset ID | Description |
|------|-----------|-------------|
| `main branch protection.json` | 18322478 | Protects the default branch — requires PR with 1 approval from a code owner, prevents deletion and force pushes |
