---
name: mpt-ext-workflow-fix-dependabot-prs
description: Process Dependabot PRs end to end: find relevant PRs, check out their branches, apply dependency-policy fixes, run checks, fix failures, amend the Dependabot commit, and push back.
---

# Fix Dependabot PRs

## Purpose

Coordinate the full SoftwareOne Dependabot PR remediation workflow for extension repositories.

## Use When

- The user wants to process one or more open Dependabot PRs in a `softwareone-platform` extension repository.
- Dependabot PRs may need dependency-policy fixes before review or merge.
- The workflow must validate the result and push fixes back to the original upstream Dependabot branches.
- Validation failures may need scoped follow-up fixes before the branch can be published.

## Do Not Use When

- The PR is not authored by Dependabot.
- The user wants to bump dependencies manually from a normal feature branch.
- The task is only to apply the dependency policy fix to an already selected PR or checked-out branch.
- The task requires changing shared dependency policy rather than applying it.
- The repository does not follow the shared Python dependency-management and validation workflow.

## Inputs

- Target repository under the `softwareone-platform` organization.
- Open Dependabot PR number, or permission to process all open Dependabot PRs in the repository.
- GitHub authentication that can read PR metadata and push to Dependabot branches in the upstream repository.
- Local Git checkout of the target upstream repository.
- Repository dependency and validation workflow that follows the shared package guidance.
- Python 3.12 or later is available as `python3` for bundled deterministic scripts.

## Shared References

Use these shared documents as the source of truth instead of restating their policy. When shared guidance is needed, resolve it from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read the same path from the `main` branch of the shared GitHub repository.

- `standards/packages-and-dependencies.md`
- `knowledge/manage-dependencies.md`
- `knowledge/build-and-checks.md`
- `standards/pull-requests.md`
- `skills/mpt-ext-task-dependabot-pr-policy-fix/SKILL.md`
- `skills/mpt-ext-task-run-repository-checks/SKILL.md`
- `skills/mpt-ext-task-fix-repository-check-failures/SKILL.md`

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them, using the resolution rule from Shared References.

2. Find the target Dependabot PRs.
- If the user provided a PR number, inspect only that PR.
- Otherwise list open Dependabot PRs in the upstream repository:

```bash
gh pr list --repo softwareone-platform/<repo> --state open --author 'dependabot[bot]' --limit 200 --json number,title,url,headRefName,baseRefName
```

- Collect PR number, title, URL, head branch, and base branch.

3. Read and classify each PR before changing anything.
- Read PR metadata, changed files, and diff.
- Verify the PR head branch is a Dependabot branch.
- Verify the changed files are dependency-related before applying this workflow.
- Use the analyzer bundled with the policy-fix task for repeatable classification:

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-dependabot-pr-policy-fix/scripts/analyze_dependabot_pr.py" \
  --metadata-json pr.json \
  --changed-files-json files.json \
  --diff-file pr.diff \
  --pretty
```

- Skip PRs that are not Dependabot-authored, are not dependency-related, or have no relevant policy signal.

4. Check out the exact Dependabot branch.
- Fetch the base and head branches from upstream.
- Check out the existing Dependabot branch directly.
- Rebase the Dependabot branch on the latest base branch before editing:

```bash
git fetch origin <base-branch> <head-branch>
git checkout <head-branch>
git pull --rebase origin <base-branch>
```

- Do not create a new work branch.

5. Apply dependency-policy fixes.
- Invoke `mpt-ext-task-dependabot-pr-policy-fix` for the selected PR or checked-out Dependabot branch.
- Keep the task scoped to dependency-policy files and dependency lock refresh.
- Record changed files and fixed rules for the final report.

6. Run repository checks.
- Invoke `mpt-ext-task-run-repository-checks` using the repository-defined validation flow.
- If the repository follows the shared validation guidance and `uv.lock` changed, run `make build` before `make check-all`.
- Preserve command output with the command that produced it.

7. Fix actionable validation failures.
- If validation fails, hand the failing output to `mpt-ext-task-fix-repository-check-failures` once; that task owns the bounded fix-and-rerun loop. Do not re-loop it from here.
- Constrain the fix scope to failures clearly caused by the Dependabot dependency change, dependency lock refresh, pre-commit pin sync, or validation fallout from those files.
- Act on its returned outcome: continue to publishing only on `fixed`; on any other outcome — including failures that are environment-related, unrelated to the Dependabot change, or that need a product or design decision — stop without committing or pushing and record the blocker.

8. Amend and push to the same Dependabot branch.
- Stage only files from the recorded changed-file list produced by the policy-fix and validation-fix steps.
- After staging, check whether there are staged changes before amending:

```bash
git add <recorded-changed-file>...
git diff --cached --quiet
```

- If there are no staged changes, skip `git commit --amend --no-edit` and `git push --force-with-lease`, then report the PR as validated with no publishable changes.
- If staged changes exist, amend the existing Dependabot commit and push it back to the same upstream branch:

```bash
git commit --amend --no-edit
git push --force-with-lease origin <head-branch>
```

- Do not create a new PR and do not push to a personal fork.

9. Report results.
- Record processed, skipped, fixed, pushed, and blocked PRs.
- Include PR number and URL, status, fixed rules, changed files, validation commands and results, amended commit SHA, push result, and skip or blocker reasons.
- Render the multi-PR report deterministically: collect the per-PR result objects into a JSON file and pass it to the bundled `render_result.py` for a stable Markdown summary.

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-workflow-fix-dependabot-prs/scripts/render_result.py" \
  --results-json results.json
```

## Guardrails

- Never process non-Dependabot PRs with this workflow.
- Never create new branches or pull requests for Dependabot remediation.
- Never push fixes anywhere except the original Dependabot branch in upstream.
- Never restate or diverge from the dependency-policy rules that `mpt-ext-task-dependabot-pr-policy-fix` owns (broad `pyproject.toml` specifiers, `opentelemetry`-family bumps, opportunistic `.pre-commit-config.yaml` edits); delegate them to that task.
- Never continue to amend or push after failed validation unless the failure has been fixed and the required validation flow passes.
- Never wrap a fix task that already owns its bounded loop in a second retry loop; invoke it once per Dependabot PR, consume its classified outcome, and stop on anything other than success.
- Never use validation auto-fix as permission to make unrelated product-code changes in a Dependabot PR.
- Never run repository-required validation steps in parallel when the shared validation workflow requires a sequence.

## Expected Outcome

Relevant open Dependabot PRs are fixed in their existing upstream branches, repository-required checks pass, amended Dependabot commits are pushed back for review, and skipped or blocked PRs are reported with precise reasons.
