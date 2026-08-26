# GitHub Access Strategy

Prefer direct GitHub API calls over `gh` when available. Some sandboxed environments (such as sbx) attach GitHub credentials to `api.github.com` requests at the network layer without exposing a token to the agent. Do not ask the user for a token and do not print, read, or persist secrets.

## Access selection sequence

Determine the repository first:

```bash
git remote get-url origin
```

Normalize the result to `OWNER/REPO` (strip `.git` suffix, handle both HTTPS and SSH URLs).

Then attempt access methods in order until one succeeds at listing PRs:

### Method 1: Direct API with ambient credentials

Ping the API:

```bash
curl -fsS https://api.github.com/user | jq -r .login
```

If this returns a login, attempt to list PRs with the API command set. If the pulls endpoint returns 403, do NOT silently accept the empty result — move to Method 2.

### Method 2: gh CLI

```bash
gh pr list --author "app/dependabot" --state open --json number,title,url,createdAt,headRefName,labels --limit 100
```

**Critical**: `gh pr list` can silently return `[]` when the token lacks `pull_requests:read` permission, because the underlying GraphQL query returns FORBIDDEN but gh swallows the error when using filters like `--author`. You MUST validate the result.

### Validating PR list results

After any method returns an empty PR list, cross-check with the repo metadata:

```bash
gh api "repos/<OWNER>/<REPO>" --jq '.open_issues_count'
```

If `open_issues_count` > 0 but the PR list is empty, the token likely lacks PR read access. Confirm by testing a direct GraphQL query:

```bash
gh api graphql -f query='{ repository(owner: "<OWNER>", name: "<REPO>") { pullRequests(states: OPEN, first: 1) { totalCount } } }' 2>&1
```

If this returns "Resource not accessible by personal access token" or similar FORBIDDEN error, the token does not have PR read permissions.

### Method 3: Unset GITHUB_TOKEN and retry

If `GITHUB_TOKEN` is set in the environment and is causing the permission failure, the keyring-stored credential may have broader scopes. Try:

```bash
env -u GITHUB_TOKEN gh pr list --author "app/dependabot" --state open --json number,title,url,createdAt,headRefName,labels --limit 100
```

If this succeeds, use `env -u GITHUB_TOKEN gh ...` for all subsequent gh commands in this session.

### Method 4: Report the permission failure

If all methods fail, stop and clearly report to the user:

> ⚠️ **Cannot access pull requests.** The active GitHub token lacks `pull_requests:read` permission. The repo reports N open issues/PRs but I cannot list them.
>
> To fix this, either:
> 1. Add `pull_requests: read` to your fine-grained PAT, or
> 2. Unset the `GITHUB_TOKEN` environment variable to let `gh` use its keyring-stored OAuth token (which has `repo` scope), or
> 3. Run `gh auth login` with a token that has appropriate scopes.

Do NOT declare "no Dependabot PRs found" if you cannot confirm PR access is working.

## API command set

Use when Method 1 succeeds (direct API with ambient credentials):

List open Dependabot PRs:

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/pulls?state=open&per_page=100&page=1" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
| jq -r '.[] | select(.user.login == "dependabot[bot]") | [.number, .title, .html_url, .created_at, .head.ref, .head.sha] | @tsv'
```

Fetch PR metadata and changed files:

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<NUMBER>" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28"

curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<NUMBER>/files?per_page=100" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28"
```

Fetch the PR diff:

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<NUMBER>" \
  -H "Accept: application/vnd.github.v3.diff" -H "X-GitHub-Api-Version: 2022-11-28"
```

Check CI status using the PR head SHA:

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/commits/<SHA>/check-runs" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
| jq -r '.check_runs[] | [.name, .status, .conclusion] | @tsv'
```

Check for existing review marker:

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/issues/<NUMBER>/comments?per_page=100" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
| jq -r '.[].body' | grep -q "dependabot-audit:v1"
```

Post a review comment (only after explicit user approval):

```bash
jq -Rs '{body: .}' /tmp/dep-review-<NUMBER>.md \
| curl -fsS -X POST "https://api.github.com/repos/<OWNER>/<REPO>/issues/<NUMBER>/comments" \
    -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    -H "Content-Type: application/json" --data-binary @-
```

Merge (merge commit, not squash):

```bash
curl -fsS -X PUT "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<NUMBER>/merge" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" -d '{"merge_method":"merge"}'
```

## gh command set

Use when Method 2 or 3 succeeds. If Method 3 was needed, prefix all commands with `env -u GITHUB_TOKEN`.

```bash
gh repo view --json nameWithOwner -q .nameWithOwner
gh pr list --author "app/dependabot" --state open --json number,title,url,createdAt,headRefName,labels --limit 100
gh pr view <NUMBER> --json title,body,url,files,headRefName,createdAt,labels
gh pr checks <NUMBER>
gh pr diff <NUMBER>
gh pr comment <NUMBER> --body-file /tmp/dep-review-<NUMBER>.md
gh pr merge <NUMBER> --merge
gh pr comment <NUMBER> --body "@dependabot rebase"
```
