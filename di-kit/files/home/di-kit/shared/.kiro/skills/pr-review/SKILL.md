---
name: pr-review
description: >
  Review an open pull request: gather all reviewer comments, evaluate feedback
  against the code, divide into quick wins and items needing discussion, agree
  an approach with the author, implement fixes as TOFIXUP commits, leave
  respectful disagreement comments where needed, and suggest resolving satisfied
  threads. Use when asked to work through PR comments, address reviewer feedback,
  or help clear outstanding review threads on a pull request.
metadata:
  author: "@huwd"
  version: "1.0.0"
---

# PR Review

Work through open reviewer comments on a pull request to a clear end state:
every thread either has a fix committed, a respectful disagreement posted, or a
suggestion to resolve.

## Workflow overview

1. Gather PR data — metadata, diff, all comment threads
2. Evaluate threads — classify as quick wins or more thought needed
3. Discuss with the author — agree approach for each thread
4. Act on agreed approach — fix or disagree
5. Suggest resolving satisfied threads

Never post comments, commit code, or resolve threads without explicit agreement
from the PR author (the user).

## GitHub Access Strategy

Follow the access strategy in [references/github-access.md](references/github-access.md). In summary:

1. Determine `OWNER/REPO` from `git remote get-url origin`
2. Try `gh` CLI first; fall back to direct API calls
3. If both fail, report the permission gap and stop

Do not ask for tokens. Do not print, read, or persist secrets.

## Step 1: Gather PR data

Fetch in a single pass:

```bash
# PR metadata, files, commits
gh pr view <NUMBER> --repo <OWNER/REPO> \
  --json number,title,body,author,headRefName,baseRefName,state,files,commits,url

# Inline review comments (line-level threads)
gh api repos/<OWNER/REPO>/pulls/<NUMBER>/comments?per_page=100 \
  --jq '.[] | {id, path, line, body, user: .user.login, created: .created_at, in_reply_to_id}'

# PR-level reviews (body + state)
gh api repos/<OWNER/REPO>/pulls/<NUMBER>/reviews?per_page=100 \
  --jq '.[] | {id, user: .user.login, state, body, submitted_at}'

# Issue-level comments (top-of-PR thread)
gh api repos/<OWNER/REPO>/issues/<NUMBER>/comments?per_page=100 \
  --jq '.[] | {id, user: .user.login, body, created: .created_at}'
```

Group inline comments into threads by tracking `in_reply_to_id`. A comment with
`in_reply_to_id: null` starts a new thread; all replies chain from it.

Read the diff for any thread whose context you need:

```bash
gh pr diff <NUMBER> --repo <OWNER/REPO>
```

## Step 2: Evaluate threads

For each thread, form a view before presenting to the author. Ask:

- **Is the reviewer correct?** Check the code, not just the comment.
- **Is there a code change required?** Not every thread needs one.
- **How much effort?** A one-liner vs a structural change.
- **Any unresolved questions?** Threads that end mid-conversation need a reply regardless.

Classify into two buckets:

**Quick win** — clear action, low effort, low risk of unintended effects:
- Reviewer is correct, fix is contained (remove a parameter, rename, add a comment)
- Thread is a Q&A that ended with a clear answer — just needs acknowledgement + resolve

**More thought needed** — needs discussion before acting:
- Fix is structural (adds infra, changes architecture, touches auth/security)
- Reviewer opinion conflicts with a documented decision in the PR
- The thread has unanswered questions you can't answer without external input
- Multiple valid approaches exist and the tradeoffs aren't obvious

## Step 3: Discuss with the author

Present your classification with a recommendation for each thread:

```
### Thread: <file>:<line> — <one-line summary>
Reviewer: <username>
Classification: Quick win / More thought needed

<Your reading of the thread and what the reviewer is asking for.>

Recommendation: <What you suggest doing — fix / disagree / reply-and-park.>
Reason: <Why this is the right call.>
```

For quick wins, propose the specific change or reply text.
For more thought needed, surface the decision that needs to be made.

Wait for the author to confirm the approach for each thread before acting.
If the author modifies your recommendation, follow their direction.

## Step 4: Act

### Agreed fixes

For each thread where the author agrees a code change is needed:

1. Implement the fix on the current branch
2. Commit with a `TOFIXUP:` prefix so it's easy to squash later:
   ```
   TOFIXUP: <short description of what this addresses>
   ```
3. Push the branch
4. Reply to the thread with a link to the commit:
   ```bash
   gh pr comment <NUMBER> --repo <OWNER/REPO> \
     --body "Good call — done in <commit-sha>. <Optional: one-sentence explanation of the approach taken.>"
   ```
   When replying to an inline thread, use the review comment reply endpoint:
   ```bash
   gh api repos/<OWNER/REPO>/pulls/comments/<THREAD-COMMENT-ID>/replies \
     -X POST -f body="Good call — done in <commit-sha>."
   ```

### Agreed non-changes (author agrees no fix needed)

Reply to the thread explaining why no change was made, linking to relevant code
or documentation in the PR that addresses the concern:

```bash
gh api repos/<OWNER/REPO>/pulls/comments/<THREAD-COMMENT-ID>/replies \
  -X POST \
  -f body="<Explanation. Link to relevant section of the PR, doc, or prior decision.>"
```

### Disagreements

When the author disagrees with a reviewer comment:

- Be direct but collegial — acknowledge what's valid in the reviewer's point
- Link to the specific code, document, or decision that supports the current approach
- Don't restate the reviewer's point back at them at length
- Don't assert without evidence — link or quote

Template:
```
Thanks for flagging this. <One sentence acknowledging the concern is reasonable.>

In this case, <explanation of why the current approach is intentional / already addressed>, 
as documented in <link to file/section/commit>. <Optional: what would need to change for 
the reviewer's suggestion to apply.>

Happy to discuss further if you see it differently.
```

Post via:
```bash
gh api repos/<OWNER/REPO>/pulls/comments/<THREAD-COMMENT-ID>/replies \
  -X POST \
  -f body="<your message>"
```

## Step 5: Suggest resolving threads

After all threads have a reply (fix link, explanation, or disagreement), suggest
which threads can be resolved:

- A thread with a committed fix and a reply pointing to it → suggest resolve
- A thread where a Q&A concluded and both sides are satisfied → suggest resolve
- A thread with an outstanding disagreement or unanswered question → do NOT suggest resolve

Present the list to the author:

```
The following threads look ready to resolve:
- <file>:<line> — <summary> (fix in <sha> / agreed no change needed)
- ...

Want me to resolve these?
```

Resolve only after explicit author confirmation:
```bash
gh api repos/<OWNER/REPO>/pulls/<NUMBER>/comments/<THREAD-ID> \
  -X PATCH -f body=... # (resolution is via the UI; suggest to the user rather than
                        # auto-resolving — GitHub's API doesn't expose a resolve endpoint
                        # for review threads directly)
```

Note: GitHub does not expose a direct API endpoint to resolve review threads.
Suggest the threads to the author and let them click Resolve in the UI, or use
the GraphQL mutation `resolveReviewThread` if available.

## Output format for the discussion step

```markdown
## PR #<N> — Thread Review

### Quick wins (<N> threads)

**1. <file>:<line> — <one-line summary>**
Reviewer: <username>
> <quoted key line from the thread>

Reading: <your interpretation>
Recommendation: <proposed fix or reply text>

---

### More thought needed (<N> threads)

**1. <location or issue comment> — <one-line summary>**
Reviewer: <username>
> <quoted key line from the thread>

Reading: <what's being asked / why it's not straightforward>
Decision needed: <the specific question the author needs to answer>

---

### Threads already resolved or self-contained
<list any that need no action>
```

## Gotchas

- **Self-review threads are common.** Authors often leave their own questions in review comments to invite discussion. These are not reviewer requests — they're open questions. Read the thread to see if a reviewer answered them before classifying.
- **Threads ending in a question need a reply.** Even if a reviewer gave useful guidance, if the author replied with a question and got no response, the thread isn't done. Reply to acknowledge and either answer or park it.
- **`in_reply_to_id` chains threads.** The top-level comment (null `in_reply_to_id`) is the anchor. Replies all reference it. When posting a reply, use the top-level comment ID as the thread anchor.
- **TOFIXUP commits are for squashing, not shipping.** They should be small and clearly named. The author will squash them before merge, so don't agonise over commit message polish.
- **Secure Pipelines parameter constraints.** In di-documentation / GDS One Login repos using the devplatform Secure Pipelines, only a specific set of CloudFormation parameters are passed by the pipeline (e.g. `Environment`, `VpcStackName`, `SigningProfileVersionArn`). Non-standard parameters will not be set. If reviewing a CF template, flag any non-standard parameters as a potential blocker — the fix is usually a Mapping keyed on `Environment` or hard-coding.
- **Disagreement ≠ dismissal.** If you're posting a disagreement on behalf of the author, make sure it acknowledges what's valid in the reviewer's point before explaining the divergence. A dismissive response damages the review relationship.
- **GitHub review thread resolution has no REST API.** You can suggest threads for the author to resolve, and you can use the GraphQL API (`resolveReviewThread` mutation), but there is no REST endpoint. Default to suggesting, not auto-resolving.

## Explicit non-goals

- Do not approve or merge the PR — that is the reviewer's decision.
- Do not re-review code that reviewers didn't comment on.
- Do not resolve threads without explicit author confirmation.
- Do not post any comment without explicit author confirmation.
- Do not commit or push without explicit author confirmation.
- Do not assess CI/CD pipeline health — only note if CI is blocking and what it's blocking.
