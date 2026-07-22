---
name: dependabot-pr-review
description: Review Dependabot pull requests in a repository. Use when asked to assess, triage, comment on, approve, merge, or decide what to do with one Dependabot PR, all open Dependabot PRs, or dependency update PRs.
metadata:
  author: "@huwd"
  version: "1.0.0"
---

# Dependabot PR Review

Review Dependabot PRs and give a clear verdict: what changed upstream, what could break, what the package touches in this codebase, and whether to merge, verify, investigate, or hold.

## Choose a Mode

- **Single-PR mode**: the user pasted or named one PR. Review that PR only.
- **Audit mode**: the user asks about all open Dependabot PRs, pending dependency updates, or says something like "check dependabot". Discover PRs with the GitHub API first, falling back to `gh`; do not ask for URLs.

If ambiguous, default to audit mode.

## GitHub Access Strategy

Prefer direct GitHub API calls over `gh` when available. Some sandboxed environments (such as sbx) attach GitHub credentials to `api.github.com` requests at the network layer without exposing a token to the agent. Do not ask the user for a token and do not print, read, or persist secrets.

### Access selection sequence

Determine the repository first:

```bash
git remote get-url origin
```

Normalize the result to `OWNER/REPO` (strip `.git` suffix, handle both HTTPS and SSH URLs).

Then attempt access methods in order until one succeeds at listing PRs:

#### Method 1: Direct API with ambient credentials

Ping the API:

```bash
curl -fsS https://api.github.com/user | jq -r .login
```

If this returns a login, attempt to list PRs with the API command set. If the pulls endpoint returns 403, do NOT silently accept the empty result — move to Method 2.

#### Method 2: gh CLI

```bash
gh pr list --author "app/dependabot" --state open --json number,title,url,createdAt,headRefName,labels --limit 100
```

**Critical**: `gh pr list` can silently return `[]` when the token lacks `pull_requests:read` permission, because the underlying GraphQL query returns FORBIDDEN but gh swallows the error when using filters like `--author`. You MUST validate the result.

#### Validating PR list results

After any method returns an empty PR list, cross-check with the repo metadata:

```bash
gh api "repos/<OWNER>/<REPO>" --jq '.open_issues_count'
```

If `open_issues_count` > 0 but the PR list is empty, the token likely lacks PR read access. Confirm by testing a direct GraphQL query:

```bash
gh api graphql -f query='{ repository(owner: "<OWNER>", name: "<REPO>") { pullRequests(states: OPEN, first: 1) { totalCount } } }' 2>&1
```

If this returns "Resource not accessible by personal access token" or similar FORBIDDEN error, the token does not have PR read permissions.

#### Method 3: Unset GITHUB_TOKEN and retry

If `GITHUB_TOKEN` is set in the environment and is causing the permission failure, the keyring-stored credential may have broader scopes. Try:

```bash
env -u GITHUB_TOKEN gh pr list --author "app/dependabot" --state open --json number,title,url,createdAt,headRefName,labels --limit 100
```

If this succeeds, use `env -u GITHUB_TOKEN gh ...` for all subsequent gh commands in this session.

#### Method 4: Report the permission failure

If all methods fail, stop and clearly report to the user:

> ⚠️ **Cannot access pull requests.** The active GitHub token lacks `pull_requests:read` permission. The repo reports N open issues/PRs but I cannot list them.
>
> To fix this, either:
> 1. Add `pull_requests: read` to your fine-grained PAT, or
> 2. Unset the `GITHUB_TOKEN` environment variable to let `gh` use its keyring-stored OAuth token (which has `repo` scope), or
> 3. Run `gh auth login` with a token that has appropriate scopes.

Do NOT declare "no Dependabot PRs found" if you cannot confirm PR access is working.

### API command set

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

### gh command set

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

## Ecosystem Detection

Before reviewing, detect which ecosystem(s) are in play by checking for these files at the repo root and in subdirectories:

| Ecosystem | Detection files | Notes |
|-----------|----------------|-------|
| Bundler (Ruby) | `Gemfile`, `Gemfile.lock` | Check for groups (:development, :test) |
| Gradle (Kotlin/Java) | `build.gradle.kts`, `settings.gradle.kts`, `gradle/libs.versions.toml` | Multi-module: check `settings.gradle.kts` for `include()` |
| Maven (Java) | `pom.xml` | May have parent POM inheritance |
| Swift (SPM) | `Package.swift`, `Package.resolved` | |
| npm (TypeScript/JS) | `package.json`, `package-lock.json` | Check for workspaces in root `package.json` |
| Docker | `Dockerfile`, `docker-compose.yml` | Digest pins (`image@sha256:...`) vs tag pins |
| GitHub Actions | `.github/workflows/*.yml` | Action version pins |

For multi-ecosystem repos, identify which ecosystem the PR targets from the changed files.

## Audit Workflow

1. Determine the repo. Follow the access selection sequence to establish a working access method.
2. List open Dependabot PRs. **Validate the result** — if the list is empty, cross-check against `open_issues_count` as described in the access strategy. Only declare "no PRs" if validated.
3. If none are open (validated), say so and stop. If the count is at or near `open-pull-requests-limit` in `.github/dependabot.yml`, flag queue saturation — it can block security PRs.
4. Analyse each PR with the single-PR workflow.
5. Produce a consolidated report:

```markdown
Reviewed N open Dependabot PRs in <repo>.

| # | Package | Bump | Type | Age | Verdict | Why |
|---|---------|------|------|-----|---------|-----|
| [#123](url) | package-name | 1.2.3 → 1.2.4 | patch | 7d | Merge | dev-only patch |
```

Sort by verdict: Merge → Verify → Investigate → Hold. Security PRs go first regardless. Within each bucket, oldest first.

Follow with a details section (15–25 lines per PR) and an overall recommendation grouped by verdict, calling out package families that should move together.

## Single-PR Workflow

### 1. Gather PR Details

Fetch PR metadata, CI status, changed files, and diff. Also read `.github/dependabot.yml` — confirm a cooldown exists for the relevant ecosystem.

Extract for each package:
- Package name, old version → new version
- Direct vs transitive dependency
- Manifest or workspace touched
- Dependency type: production, development, test, optional, peer, toolchain
- Bump type: patch, minor, major, or pre-1.0 minor (treat as major-equivalent)
- Whether advisory-driven (from PR body, labels, CVE/GHSA references)

For grouped PRs, assess every package. If one requires escalation, the whole PR inherits that concern.

### 1b. Read PR Conversation

Fetch all comments and review threads on the PR before forming a verdict. Prior discussion may contain important context — reviewer concerns, deployment notes, related PRs, or unresolved debate that should inform the recommendation.

**API command set:**

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/issues/<NUMBER>/comments?per_page=100" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
| jq -r '.[] | select(.user.login != "dependabot[bot]") | {user: .user.login, created: .created_at, body: .body}'
```

Also fetch review comments (inline code comments):

```bash
curl -fsS "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<NUMBER>/reviews?per_page=100" \
  -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
| jq -r '.[] | select(.state != "PENDING") | {user: .user.login, state: .state, body: .body}'
```

**gh command set:**

```bash
gh pr view <NUMBER> --json comments,reviews --jq '.comments[] | select(.author.login != "dependabot[bot]") | {user: .author.login, created: .createdAt, body: .body}'
gh pr view <NUMBER> --json reviews --jq '.reviews[] | {user: .author.login, state: .state, body: .body}'
```

**What to look for:**
- Unresolved objections or requested changes from reviewers
- Context about why a previous version of this PR was rejected or held
- Notes about related PRs that should merge together
- Deployment or runtime concerns raised by team members
- Dependabot command comments (`@dependabot rebase`, `@dependabot ignore`) that signal team intent
- Approval reviews that indicate the team already assessed the change

**How to use this context:**
- If a reviewer raised a concern that remains unresolved, note it in the review and factor it into the verdict
- If the team already approved but hasn't merged, flag this — it may just need someone to click merge
- If `@dependabot ignore` was discussed but not posted, note the team's intent
- Do not override human reviewer decisions — if a human requested changes, the verdict should reflect that regardless of your own analysis
- Surface the conversation in a "PR Discussion" section of your review output when relevant points exist

### 2. Apply Hard Gates

CI is a hard gate:
- **CI failed**: do not merge. Note the failing job.
- **CI pending**: wait. Do not merge on partial green.
- **Advisory-driven + CI passing**: merge on the advisory fast path.
- **Advisory-driven + CI failing**: block and flag to the user.

#### Cooldown — already satisfied by Dependabot

Dependabot applies a cooldown **before** opening a PR. A new version is not proposed for update until the configured cooldown period (or the 3-day default) has elapsed since its release date. By the time a PR exists, the cooldown has already passed. **Do not add a second cooldown based on the PR creation date.**

When reviewing, verify that a `cooldown` section exists in `.github/dependabot.yml` for the relevant ecosystem. If it is absent, note this as a *configuration recommendation* (the 3-day default still applies, but an explicit config is best practice). This is informational — it is not a reason to hold or block a merge.

### 3. Review Upstream Changes

Read changelog, release notes, or commit titles for the exact version range. Try in order:
1. PR body links from Dependabot
2. GitHub releases/tags for the source repo
3. Changelog files (`CHANGELOG.md`, `HISTORY.md`)
4. Package registry metadata (Maven Central, npm, Swift Package Index)
5. Package diff tooling as a last resort

Prioritise:
- **Breaking changes**: removed/renamed APIs, changed defaults, dropped runtime support, peer dependency tightening
- **Deprecations**
- **Security fixes**
- **Notable bug fixes relevant to this repo**

If no changelog is findable, say so explicitly. Do not invent release notes.

### 4. Check Codebase Impact

Search actual usage before deciding risk. For each ecosystem:

**Gradle (Kotlin/Java):**
- Check `gradle/libs.versions.toml` for the version declaration
- Search all `build.gradle.kts` files for the dependency alias or direct coordinate
- For multi-module projects: a dependency declared centrally may be used in any subproject
- Check for Gradle platform/BOM constraints that pin transitive versions

**Maven:**
- Check `pom.xml` `<dependencies>` and `<dependencyManagement>`
- Check parent POM inheritance for version declarations
- Search for imports of the package's classes

**Swift (SPM):**
- Check `Package.swift` for the dependency declaration
- Check `Package.resolved` for transitive impact
- Search source files for `import <ModuleName>`

**npm:**
- Check root and workspace-level `package.json` files
- Workspace hoisting: a dependency in one workspace may affect others
- Search for `import`/`require` statements

**Docker:**
- A digest-only bump (`image@sha256:aaa` → `image@sha256:bbb`) does NOT guarantee the same runtime version. Dependabot tracks digests without understanding the image contents.
- **Always verify the runtime version inside the new image.** Query the Docker registry API for the image config and check environment variables (`RUBY_VERSION`, `NODE_VERSION`, `PYTHON_VERSION`, `GOLANG_VERSION`, etc.):
  ```bash
  TOKEN=$(curl -fsS "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/<IMAGE>:pull" | jq -r .token)
  # Get the amd64 manifest from the manifest list
  AMD64=$(curl -fsS "https://registry-1.docker.io/v2/library/<IMAGE>/manifests/<NEW_DIGEST>" \
    -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.oci.image.index.v1+json" \
    | jq -r '.manifests[] | select(.platform.architecture=="amd64" and .platform.os=="linux") | .digest')
  # Get the config blob digest
  CONFIG=$(curl -fsS "https://registry-1.docker.io/v2/library/<IMAGE>/manifests/$AMD64" \
    -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.oci.image.manifest.v1+json" \
    | jq -r '.config.digest')
  # Inspect the config for version env vars
  curl -fsSL "https://registry-1.docker.io/v2/library/<IMAGE>/blobs/$CONFIG" \
    -H "Authorization: Bearer $TOKEN" | jq '.config.Env[]'
  ```
- If the runtime version has changed, check for version files that must stay in sync (`.ruby-version`, `.node-version`, `.python-version`, `.tool-versions`)
- Check if CI setup actions (e.g., `ruby/setup-ruby`, `actions/setup-python`) read those version files — a mismatch means CI tests one version but the container runs another
- Check if lockfiles (`Gemfile.lock`, `package-lock.json`, `poetry.lock`) need regenerating for the new runtime version
- If the Dockerfile has a comment annotating the tag (e.g., `# 4.0.5-alpine3.22`), it will be stale after a version change — flag it
- Verdict: **Hold** if the digest introduces a version change and version files / lockfiles are not updated in the same PR

**General for all ecosystems:**
- Cross-reference breaking changes against actual usage
- State either `affected` with file paths and required fix, or `not used here` with the search basis
- Flag extra scrutiny for: auth, cryptography, network/HTTP, database, framework/runtime, build system, deployment, and cloud SDK packages

**Package families** — avoid merging one PR while siblings remain stale:
- Spring Boot + Spring Security + Spring Cloud
- AWS SDK v2 modules (`software.amazon.awssdk:*`)
- Smithy packages
- Ktor client/server/plugins
- Jest/Vitest, ESLint ecosystem, TypeScript/ts-node
- SwiftUI/Combine framework-level packages
- GitHub Actions (shared major version pins)

### 5. Assign a Verdict

| Verdict | When |
|---------|------|
| **Merge** | CI passes, cooldown/advisory rule satisfied, changelog clean, codebase impact low or understood |
| **Verify** | Likely safe but a specific runtime/manual check needed that CI may not cover |
| **Investigate** | Human judgment needed — risk or compatibility unclear |
| **Hold** | Breaking changes, failed/pending CI, package-family mismatch, or code changes needed first |

Risk guide:

| Factor | Lower risk | Higher risk |
|--------|------------|-------------|
| Bump | patch on stable version | major or pre-1.0 minor |
| Scope | dev/test/tooling only | production runtime |
| Usage | isolated or unused | widespread or hot path |
| Changelog | bug fixes only | API/default/runtime changes |
| Package | formatter/linter/types | auth/crypto/network/framework/deploy |
| Lockfile | small, expected diff | broad transitive churn |
| Family | standalone or complete set | partial sibling bump |
| Security | no advisory | advisory — prioritise once CI passes |

Do not recommend "run the full test suite" as the main action — CI owns that. Instead, name the specific thing CI may not catch: runtime config, deployment behaviour, generated types, local dev server, external service compatibility, deprecation warnings.

## Output Format

For one PR:

```markdown
## Dependabot Review: `<package>` (<old> → <new>)

### Bump Type
[patch/minor/major/pre] — [one line about risk]

### What Changed
[Breaking changes first, then deprecations, security fixes, relevant bug fixes. If quiet: "No breaking changes or deprecations found."]

### Breaking Changes in This Codebase
[Only if applicable: affected file + concrete fix. Otherwise omit this section.]

### Codebase Impact
[Grouped list of touched areas, not an exhaustive file dump.]

### PR Discussion
[Only if the PR has non-bot comments or reviews. Summarise key points: reviewer concerns, approvals, context shared, unresolved debate. If no human discussion exists, omit this section.]

### Recommendation
[Merge / Verify / Investigate / Hold] — [1-3 sentences with reason and specific check.]
```

For audit mode, put the summary table first, then 15–25 lines per PR in the details section.

## Posting Findings to PRs

Always ask before posting. Never comment automatically.
- Single PR: `Want me to post this review as a comment on PR #<N>? (yes / no)`
- Audit mode: `Want me to post each review as a comment on its PR? (yes / no / selective)`

Before posting, check for an existing `dependabot-audit:v1` marker. If found, ask whether to skip or repost. Default to skipping.

Comment shape:

```markdown
## Dependabot review

**Verdict:** <Merge / Verify / Investigate / Hold>

<one-line reason>

<details>
<summary>Full review</summary>

<full per-PR review>

</details>

<!-- dependabot-audit:v1 -->
```

Do not add attribution or a generated-by signature.

## Merge Behaviour

Use a merge commit (not squash) so the Dependabot commit remains visible for audit history.

After merging one Dependabot PR in a batch, remaining PRs may need rebasing:

```bash
gh pr comment <NUMBER> --body "@dependabot rebase"
```

Re-check CI before any further merge.

## Gotchas

- **Docker digest ≠ same version rebuild**: Dependabot tracks Docker images by digest. When a Dockerfile uses `image@sha256:...` (digest pinning without a tag constraint), Dependabot will propose the newest digest for that image — which may be a completely different runtime version (e.g., Ruby 4.0.5 → 4.0.6), not just a security rebuild of the same version. The Dockerfile comment (e.g., `# 4.0.5-alpine3.22`) is not machine-read and will be stale. Always inspect the image config via the registry API to confirm the actual `*_VERSION` env var. Cross-reference with `.ruby-version` / `.node-version` / `.python-version`. See [alphagov/gds-way#1242](https://github.com/alphagov/gds-way/pull/1242) for a real example where a "digest bump" was actually a Ruby minor version upgrade.
- **Cooldown is pre-PR, not post-PR**: Dependabot applies cooldown *before* opening a PR. The PR creation date is always *after* the cooldown window has elapsed. Never calculate an "eligible after" date by adding cooldown days to the PR creation date — that double-counts the cooldown and incorrectly blocks merges.
- **Silent permission failures**: `gh pr list --author "app/dependabot"` returns `[]` (not an error) when the token lacks `pull_requests:read`. This is because gh uses GraphQL which returns FORBIDDEN at the field level but gh treats a filtered empty result as valid. Always validate empty results against `open_issues_count`. A fine-grained PAT with repo metadata access but without `pull_requests:read` is a common misconfiguration — the `GITHUB_TOKEN` env var overrides any keyring-stored OAuth tokens that might have broader scopes.
- Gradle version catalogs (`libs.versions.toml`) declare versions centrally but the dependency may be used across many subprojects — search all `build.gradle.kts` files, not just the root.
- npm workspaces hoist dependencies to root `node_modules`. A dependency in one workspace `package.json` may not have a separate lockfile entry.
- Pre-1.0 semver minors (0.x.y → 0.x+1.0) should be treated as major-equivalent.
- Some One Login repos use AWS CodePipeline in addition to GitHub Actions. If GitHub Actions CI is green but the repo has a CodePipeline deployment stage, note that deployment-level verification is outside this skill's scope.
- Swift Package Manager resolves versions from `Package.swift` requirements but `Package.resolved` shows what was actually resolved — always check both.
- Gradle lockfiles (`gradle.lockfile`) may not exist in all repos. If absent, transitive dependency changes are invisible in the diff — flag this and rely on changelog analysis.
- Maven parent POM versions may be inherited from `<parent>` — check whether the version is declared locally or inherited.

## Explicit Non-Goals

- Do not merge major version bumps automatically.
- Do not merge PRs with failed or pending required CI.
- Do not apply a reviewer-side cooldown — Dependabot already enforces cooldown before opening a PR. If a PR is open, cooldown has passed.
- Do not perform speculative compatibility analysis when changelog evidence suggests a breaking change — escalate with concrete concerns.
- Do not post comments without explicit user approval.
- Do not assess deployment pipeline health (CodePipeline, etc.) — only GitHub CI status.
