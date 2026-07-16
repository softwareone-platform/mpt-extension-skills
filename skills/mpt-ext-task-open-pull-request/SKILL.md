---
name: mpt-ext-task-open-pull-request
description: Only open or update a repository-compliant pull request to publish committed work, reusing the existing PR instead of duplicating. Does not update docs, run checks, or transition Jira.
---

# Open Pull Request

## Purpose

Create or update a repository-compliant pull request for committed work.

## Use When

- The user wants to open a pull request for the current branch.
- The user wants to update the title or description of an existing pull request.
- The task requires applying repository PR rules before publishing work for review.
- The branch already contains the intended committed changes.

## Do Not Use When

- The task is to create or switch branches.
- The task is to create the commit itself.
- The task is to transition Jira issue state.
- The task is to handle review comments after the pull request already exists.

## Inputs

- Current branch or explicit head branch.
- Optional explicit base branch.
- Optional Jira issue key for the work being published.
- GitHub authentication that can read and create or edit pull requests for the target repository.
- Local Git checkout and network access needed for the repository-supported GitHub tooling.
- Jira authentication is required only when the task must emit a Jira item URL from `acli jira auth status`.
- Repository PR rules from repo docs and shared standards.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Resolve the target PR context.
- Determine the current repository and head branch.
- Determine the intended base branch from repo context or user direction.
- Use `mpt-ext-tool-gh-pr-ops` to check whether a PR already exists for the branch.

3. Read PR rules before mutation.
- Use repository PR rules from repo docs first.
- When the repository relies on this shared package standard for PR formatting, read `standards/pull-requests.md` using the shared-doc resolution rule from the repository context step, and use it as the source of truth.
- Build the complete PR title and description before creating the PR. Follow `standards/pull-requests.md` for the description-at-creation rule and the AI-generated warning line; `mpt-ext-tool-gh-pr-ops` sets them atomically.
- Render the title deterministically with the bundled `render_pr_title.py` so the Jira key, the summary, and any `[HF]`/`[BACKPORT]` marker match what the shared Danger action enforces:

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-open-pull-request/scripts/render_pr_title.py" \
  --jira-key MPT-1234 \
  --summary "<short summary>" \
  --kind feature \
  --base-branch main
```

4. Create or update the PR.
- If no PR exists for the branch, create a new PR through `mpt-ext-tool-gh-pr-ops`, which sets the complete description at creation (or uses the draft-then-ready flow when it cannot be finalized yet).
- If a PR already exists for the branch, update the existing PR instead of creating a duplicate.

5. Report the result clearly.
- Show whether the PR was created or updated.
- Show the PR title.
- Show the PR URL.
- When the Jira issue key is available, try to resolve the Jira site through `acli jira auth status` and build the Jira item URL as `https://<site>/browse/<issue-key>`.
- Include testing status in the user-facing result message.
- Use the bundled deterministic script to render the compact user-facing output after successful PR creation or update:

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-open-pull-request/scripts/render_result.py" \
  --pr-url "<pr-url>" \
  --jira-site "<site-from-acli-jira-auth-status>" \
  --jira-key MPT-1234 \
  --testing "<testing-status>"
```

- If the Jira item URL is not available safely, omit that line instead of inventing it.
- If `acli jira auth status` does not return a reliable site value, omit the `Jira:` line instead of inventing it.
- Show blockers clearly when auth, permissions, missing branch context, or GitHub API failures prevent the operation.

## Guardrails

- Never create a duplicate PR when one already exists for the branch.
- Never open a PR with a placeholder body and fill it in later; rely on `mpt-ext-tool-gh-pr-ops` and `standards/pull-requests.md` for the description-at-creation and draft-then-ready flow.
- Never invent PR formatting rules; read repository context first.
- Never mix commit creation, branch creation, or Jira transitions into this task.
- Never silently choose the wrong base branch when repo context or user intent is ambiguous.

## Bundled Resources

- `scripts/render_result.py`
  - Inputs: PR URL, testing status, optional Jira site, and optional Jira key
  - Output: compact user-facing `PR`, optional `Jira`, and `Testing` lines
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-open-pull-request/scripts/render_result.py`
- `scripts/render_pr_title.py`
  - Inputs: `--jira-key`, `--summary`, `--kind {feature,bugfix,hotfix,backport}` (default `feature`), `--base-branch` (default `main`), optional `--json`
  - Output: the PR title `[MARKER ]<JIRA-ID> <summary>`; validates the Jira key and rejects a Conventional Commit prefix in the summary; adds `[HF]`/`[BACKPORT]` only for release-branch PRs
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-open-pull-request/scripts/render_pr_title.py`

## Expected Outcome

The current branch has a repository-compliant pull request that was either created or updated successfully, or the task stops with a clear blocker that explains what must be fixed before the PR can be opened.
