---
name: mpt-ext-workflow-hotfix-backport
description: Use when a hotfix or backport must carry an existing main PR onto the active release branch and produce a validated release PR. Orchestrates the cherry-pick, validation, release PR, and Jira updates.
---

# Hotfix And Backport

## Purpose

Coordinate release-branch hotfix and backport work after the corresponding change has been prepared for `main`.

## Use When

- The user wants to backport an open or merged `main` pull request to the active release branch.
- The user wants to prepare a hotfix release-branch PR after the fix has been opened for `main`.
- The task requires finding the source `main` PR from Jira or an explicit PR, selecting the active `release/*` branch, creating a release-branch work branch, cherry-picking source PR commits one by one, validating the result, and opening or updating the release PR.
- Jira state needs to remain aligned with the hotfix or backport review flow.

## Do Not Use When

- No open or merged source pull request exists for `main`.
- The user only wants to create a normal feature or bugfix branch from `main`.
- The task is only to cherry-pick a commit without opening a pull request or managing review state.
- The pull request has already merged and the only remaining action is final Jira handoff.
- The request is to change release-branch or backport policy rather than apply it.

## Inputs

- Jira issue key for the hotfix or backport work.
- Optional explicit original `main` pull request number. If omitted, find the source PR from the Jira issue key.
- Jira issue type used to classify the mode:
  - `Bug` means `hotfix`
  - every other issue type means `backport`
- Jira fixVersions used to verify the issue is marked for the matching hotfix or backport release workflow.
- Optional explicit target release branch when the active release branch cannot be resolved safely.
- Repository validation requirements from repo docs.
- GitHub authentication that can read PR metadata, push branches, and create or update pull requests.
- Jira authentication for review-state updates.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Shared References

Use these shared documents and skills as the source of truth instead of restating their policy. When shared guidance is needed, resolve it from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read the same path from the `main` branch of the shared GitHub repository.

- `standards/pull-requests.md`
- `knowledge/backports.md`
- `knowledge/build-and-checks.md`
- `skills/mpt-ext-tool-gh-pr-ops/SKILL.md`
- `skills/mpt-ext-tool-git-branch-ops/SKILL.md`
- `skills/mpt-ext-task-run-repository-checks/SKILL.md`
- `skills/mpt-ext-task-fix-repository-check-failures/SKILL.md`
- `skills/mpt-ext-task-open-pull-request/SKILL.md`
- `skills/mpt-ext-task-move-jira-to-code-review/SKILL.md`

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs using the resolution rule from Shared References.

2. Find and confirm the source `main` pull request.
- Use the Jira issue key as the default workflow input.
- Search open and merged pull requests whose title, branch name, body, or linked metadata contains the Jira issue key.
- If the user provided an explicit pull request, inspect that PR instead of searching by Jira key.
- Stop and ask the user to choose when multiple matching source PRs target `main`.
- Stop when no open or merged source PR targeting `main` can be found.

3. Confirm the release workflow mode.
- Read the Jira issue type before classifying the work.
- Use the bundled context script after the Jira issue and original `main` PR have been read. The script applies the classification rule from `knowledge/backports.md`: `Bug` means `hotfix`, and every other issue type means `backport`.

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-workflow-hotfix-backport/scripts/render_release_context.py" \
  --jira-json /tmp/jira_issue.json \
  --pr-json /tmp/main_pr.json \
  --target-release-branch release/5 \
  --pretty
```

- Use the script output fields `mode`, `pr_marker`, `branch_prefix`, `release_branch_name`, and `blockers`.
- Use the script output fields `fix_version_ok`, `matching_fix_versions`, and `needs_fix_version_confirmation` to decide whether a Jira fix version update is needed.
- Stop and report the script blockers when `ready` is `false`.
- For a hotfix, verify that the fix has already been opened for `main`, or stop and send the normal `main` work to review first.
- For a backport, verify that the source pull request is open or merged and targets `main`.

4. Verify Jira fix version.
- If `fix_version_ok` is `true`, preserve the existing matching fix version.
- If `needs_fix_version_confirmation` is `true`, ask the user whether the matching `hotfix` or `backport` fix version should be added before editing Jira.
- If the user confirms, add the correct fix version through `mpt-ext-tool-jira-workitem-ops`, then re-read the Jira issue and rerun the bundled context script.
- If the user declines or the correct fix version cannot be resolved safely, stop and report the blocker.
- Never edit Jira fixVersions without explicit user confirmation when the matching marker is missing.

5. Resolve the source commits.
- Use `mpt-ext-tool-gh-pr-ops` to inspect the original `main` pull request.
- Read the source pull request commit list in PR order.
- Use the `source_commits` values from the bundled context script as the cherry-pick source.
- Stop when the script reports `source_pr_not_open_or_merged`, `source_pr_commits_missing`, or a non-`main` source PR base.

6. Resolve the target release branch.
- Use the active release branch rule from `standards/pull-requests.md`.
- Prefer `mpt-ext-tool-git-branch-ops` release-branch resolution for `hotfix` or `backport`.
- Stop and ask for the target release branch when no active `release/*` branch can be resolved or multiple candidates are ambiguous.

7. Create the release work branch.
- Fetch and update the target release branch.
- Create the new branch from the release branch using the `release_branch_name` value from the bundled context script.
- Stop instead of reusing an existing branch unless the user explicitly asked to continue that branch.

8. Cherry-pick the source commits.
- Cherry-pick each commit from the `source_commits` list into the release work branch one by one, preserving the script output order.
- If conflicts occur, resolve only the release-branch equivalent of the original fix.
- Do not merge `main` into the release branch.

9. Validate the release branch result.
- Use `mpt-ext-task-run-repository-checks` to run the repository-required validation flow.
- If checks fail, hand the failing output to `mpt-ext-task-fix-repository-check-failures` once; that task owns the bounded fix-and-rerun loop. Do not re-loop it from here.
- Constrain the fix scope to failures caused by the hotfix or backport.
- Act on its returned outcome: continue to publishing only on `fixed`; on any other outcome — including failures that are unrelated, environment-related, or that require a product decision — stop without pushing or opening the release PR and record the blocker.

10. Publish the release pull request.
- Publish only after the repository-required validation flow passes.
- Push the release work branch.
- Use `mpt-ext-task-open-pull-request` with the target release branch as the explicit base branch.
- Apply the release-branch PR title marker from the bundled context script `pr_marker` field.

11. Move Jira to review when ready.
- Use `mpt-ext-task-move-jira-to-code-review` after the release PR is open or updated and validation status is known.
- If the main PR still needs review or merge before the release PR should proceed, report that blocker instead of moving Jira forward.

12. Report the result clearly.
- Use the bundled result script to render the final report after the release PR and Jira transition steps:

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-workflow-hotfix-backport/scripts/render_result.py" \
  --context-json /tmp/release_context.json \
  --release-pr-url "<release-pr-url>" \
  --validation-command "make check-all" \
  --validation-status "passed" \
  --jira-status "moved to Code Review"
```

- State the workflow mode, source `main` PR, source commits, Jira fix version state, target release branch, release work branch, release PR URL, validation result, and Jira transition result.
- Surface blockers with the exact missing condition: missing source PR, source PR not open or merged, source PR not targeting `main`, missing source commits, missing matching fix version, missing release branch, cherry-pick conflict, failing validation, push failure, PR creation failure, or Jira transition failure.

## Guardrails

- Never create the release-branch PR before the corresponding open or merged `main` PR exists.
- Never override Jira issue type based classification without explicit user direction.
- Never add a missing hotfix or backport fix version without asking the user first.
- Never backport from an arbitrary feature branch; use the commits from the source pull request that targets `main`.
- Never squash the source PR commit list into one cherry-pick when the PR has multiple commits.
- Never merge `main` into a release branch as part of this workflow.
- Never silently choose a release branch when active release branch resolution is ambiguous.
- Never skip repository-required validation before opening or updating the release PR.
- Never push or open the release PR while validation is failing.
- Never wrap a fix task that already owns its bounded loop in a second retry loop; invoke it once, consume its classified outcome, and stop on anything other than success.
- Never use this workflow to change shared hotfix, backport, or release-branch policy.
- Prefer narrower task or tool skills when the user only asked for one step of the workflow.

## Bundled Resources

- `scripts/render_release_context.py`
  - Inputs: Jira issue JSON, original `main` PR JSON, optional Jira key or summary override, and optional target release branch.
  - Output: JSON with `mode`, `pr_marker`, `branch_prefix`, `release_branch_name`, `fix_version_ok`, `matching_fix_versions`, `needs_fix_version_confirmation`, `source_commits`, `blockers`, and `ready`.
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-workflow-hotfix-backport/scripts/render_release_context.py`
- `scripts/render_result.py`
  - Inputs: release context JSON plus release PR, validation, and Jira transition status.
  - Output: compact user-facing release workflow report.
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-workflow-hotfix-backport/scripts/render_result.py`

## Expected Outcome

A hotfix or backport release-branch pull request is created or updated from the correct source `main` pull request commits, validated against repository rules, and handed off in Jira for review, or the workflow stops with a precise blocker.
