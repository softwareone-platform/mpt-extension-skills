# Review Loop Operations

Operational detail for `mpt-ext-workflow-coderabbit-review-loop`: capture commands, the waiting escalation ladder, CodeRabbit command semantics, and the report templates.

## State capture (start of every iteration)

Every agent command runs in a fresh shell, so a block that sets a variable cannot rely on it later. Keep the capture in **one** block that defines everything it uses, and substitute the angle-bracket placeholders with real values.

`gh pr view` and `gh api graphql` are two requests, so a push, review, or new thread landing between them would let the evaluator mix two different PR states. Capture both, then confirm the PR did not move underneath the pair, and recapture once if it did:

```bash
workdir="$(mktemp -d)"; trap 'rm -rf "$workdir"' EXIT
# pr must be the resolved PR *number*: the GraphQL query declares $pr as Int!.
pr=<pr-number>; owner=<owner>; repo=<repo>; after=null

before="$(gh pr view "$pr" --json headRefOid,updatedAt --jq '.headRefOid + "|" + .updatedAt')" || exit 1

gh pr view "$pr" --json reviews,latestReviews,statusCheckRollup,headRefOid > "$workdir/pr.json" || exit 1

gh api graphql \
  -F owner="$owner" -F repo="$repo" -F pr="$pr" -F after="$after" \
  -f query='
    query($owner: String!, $repo: String!, $pr: Int!, $after: String) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $pr) {
          reviewThreads(first: 100, after: $after) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              isResolved
              isOutdated
              path
              line
              comments(first: 30) {
                nodes { author { login } body createdAt }
              }
              lastComment: comments(last: 1) {
                nodes { author { login } body createdAt }
              }
            }
          }
        }
      }
    }' > "$workdir/threads.json" || exit 1

after_state="$(gh pr view "$pr" --json headRefOid,updatedAt --jq '.headRefOid + "|" + .updatedAt')" || exit 1
[ "$before" = "$after_state" ] || echo "PR changed mid-capture; recapture before evaluating"
```

- The `workdir` is created here and used by the evaluator invocation; keep both in the same block, or substitute a real path in each command. The `trap` removes the directory when the shell exits, so copy the run report out of it before the block ends (or point the report at a path outside it).
- A `gh` failure must stop the capture: each call is guarded with `|| exit 1`, because a truncated `pr.json` would otherwise reach the evaluator as invalid JSON.
- Pass `after=null` for the first page. When `pageInfo.hasNextPage` is true, refetch with `after` set to `endCursor` and merge all `nodes` into one list before evaluating — the evaluator now **refuses** a payload whose `pageInfo.hasNextPage` is true rather than silently classifying a truncated set.
- The `lastComment` alias exists because `comments(first: 30)` can truncate a long thread: the evaluator takes the thread's origin from the first `comments` node and the "awaiting response" check from `lastComment` (falling back to the last `comments` node when the alias is absent).
- The evaluator accepts the full GraphQL envelope, the `reviewThreads` object, a `{nodes: [...]}` object, or a bare thread list.

## Evaluator output

`evaluate_review_cycle.py` prints one JSON object:

| Field | Meaning |
|---|---|
| `coderabbit.approved` | Effective CodeRabbit decision is `APPROVED`. Reviews are ordered by `submittedAt` only when every one carries a parseable timestamp; otherwise array order decides, so an untimestamped newer verdict is never outranked. A trailing `COMMENTED` summary never masks the decision. |
| `coderabbit.approval_is_current` | Whether the approval reviewed the current code. `true`/`false` from `--head-sha` vs the review's `commit.oid` when both are present, else from `submittedAt` vs `--since`; `null` when neither could decide. The loop's `approved` exit requires `true`. |
| `decision_commit_oid` | The commit the effective decision was submitted against, when the payload carries it. `--head-sha` may be abbreviated (7+ chars); it is matched as a prefix, never by exact equality. |
| `new_review_since` | CodeRabbit submitted any review strictly after `--since`; `null` when `--since` was not passed. |
| `actionable_threads` | Unresolved CodeRabbit threads whose last comment is CodeRabbit's — the ones awaiting an agent response. |
| `unresolved_bot_threads` | All unresolved CodeRabbit-initiated threads, including ones already answered. |
| `fingerprint` | Stable content hash of the actionable threads, keyed on path plus the full normalized comment body. The line number is deliberately excluded: this loop force-pushes every iteration, which shifts lines and nulls them on outdated threads. |
| `no_progress` | Actionable threads exist and their fingerprint equals `--previous-fingerprint`: the loop is not converging. |
| `checks` | Status-check summary: `state`, `ok`, `passing`, `pending`, `failing`. `ok` is true for `success` and for `none` (a PR with no checks configured must not deadlock the gate). |
| `exit_gate` | `{ok, reasons}` — the loop's terminal condition: CodeRabbit approved, the approval confirmed against the current head, and required checks green. `reasons` names each blocker. Branch on this, not on `approved` alone. |

## Waiting escalation ladder

One polling round is one `wait_for_coderabbit.py` invocation (default budget 540s, interval 90s). A `new_review` outcome at any point ends the ladder and returns to evaluation. The waiter counts only reviews carrying a verdict (APPROVED / CHANGES_REQUESTED / DISMISSED) and, when `--head-sha` is passed, only reviews of that commit — CodeRabbit records every chat auto-reply as a COMMENTED review, so counting those would end the wait on a reply to the loop's own thread replies.

Every `new_review` outcome goes to step 7 — record the pass, check the cap — before the next evaluation, including a wait entered with no work done. A no-work pass still consumes an iteration; exempting it would put the step 3 → step 6 → step 3 cycle outside the cap and make both the loop and its per-iteration nudge budget unbounded.

Each polling round outlives the default command timeout, so raise the timeout past the budget (or run the round in the background and collect its result) before invoking the waiter.

| Stage | Action | On continued silence |
|---|---|---|
| 1 | Two polling rounds (~18 min) | Go to stage 2 |
| 2 | Inspect the round's `errors` / `last_error` | Fetches were themselves failing → stop `environment-blocker` and report `last_error`. Otherwise → stage 3 |
| 3 | Fetch the status page to a file, check `curl`'s exit status, then classify it (see below) | Not operational → stop `coderabbit-degraded` with incident details. Fetch failed → record "status unknown", go to stage 4. Operational → stage 4 |
| 4 | Post one `@coderabbitai review` nudge (max one per iteration), two polling rounds | Go to stage 5 |
| 5 | If the full-review recovery is unused this run: post `@coderabbitai full review`, two polling rounds | Go to stage 6 (or directly to 6 when recovery was already used) |
| 6 | — | Stop `coderabbit-unresponsive` |

Stage 3 command:

```bash
if curl -fsS --max-time 30 https://status.coderabbit.ai/summary.json > <workdir>/status.json; then
  python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-workflow-coderabbit-review-loop/scripts/check_coderabbit_status.py" < <workdir>/status.json
else
  echo "status unknown"   # take the stage-3 "fetch failed" branch; do not classify a partial file
fi
```

Fetch to a file and test `curl`'s own exit status before classifying. In a `curl ... | check_coderabbit_status.py` pipeline the shell reports only the classifier's status, so a `curl` that emits a complete payload and then fails would be read as a healthy result (use `set -o pipefail` if you do pipe).

A `wait_for_coderabbit.py` `error` outcome (a run of failed polls, e.g. `gh` auth broke) is an environment blocker: stop and report it instead of continuing the ladder. A `timeout` carrying a non-zero `errors` count is the same situation — check `last_error` before reading the round as CodeRabbit's silence.

## CodeRabbit commands used by the loop

| Command | Semantics | Loop usage |
|---|---|---|
| `@coderabbitai review` | Incremental review: keeps CodeRabbit's earlier comments in consideration and reviews only the new changes | Nudge after a push it ignored, and the fresh-verdict request after a reply-only iteration; at most one per iteration |
| `@coderabbitai full review` | Fresh review: discards CodeRabbit's prior comment state and re-reviews the whole PR | Recovery from **silence** that survives a nudge (e.g. after repeated amend + force-push history rewrites); at most one per run. Never the answer to `no_progress`: re-reviewing unchanged code re-raises the identical findings, so it reproduces the stalemate instead of breaking it |
| `@coderabbitai resolve`, `approve`, `pause`, `resume` | Bulk-resolve threads / approve / stop reviews | Never posted by this loop |

Nudge and recovery comments are agent-written PR comments: post them through `mpt-ext-tool-gh-pr-ops` with the command on its own line and the required `🤖 Generated by AI` trailer.

## Iteration report entry template

Append one entry per iteration to the run report file:

```markdown
## Iteration N/<cap> — <UTC timestamp>

- Actionable CodeRabbit threads at start: <count> (<ids or paths>)
- Fixed: <list: thread → change summary>
- Answered only: <list: thread → reply gist>
- Skipped (needs user): <list: thread → reason>
- Human activity observed: <none | list>
- Validation: <checks run and result>
- Commit: <SHA> · pushed at <ISO time>
- Changes this iteration: <previous-head> → <new-head>

```text
<git diff --stat output>
```

- Waiting: <rounds used>, nudges: <none | review | full review>, status page: <not checked | operational | degraded: detail>
- CodeRabbit response: <verdict/state, new threads count>
- Fingerprint: <sha256:...> (previous: <sha256:... | none>)
```

## Final report template

```markdown
# CodeRabbit review loop — <repo> PR #<number>

- Outcome: <approved | iteration-limit-reached | non-converging | coderabbit-unresponsive | coderabbit-degraded | checks-failing | validation-blocked | commit-blocked | push-blocked | environment-blocker | pr-mismatch | needs-user-input>
- Iterations used: <N>/<cap>
- Final CodeRabbit decision: <state>
- CI checks (part of the exit gate): <state; failing/pending names>
- Left for the user: <skipped bot comments, untouched human threads, surfaced directives | none>

<iteration entries>
```
