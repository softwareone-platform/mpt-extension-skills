---
name: mpt-ext-task-apply-dashboard-jira-decision
description: Apply one approved dashboard-failure Jira decision: create, update, reopen, merge, or skip an MPT bug with dashboard evidence fields.
---

# Apply Dashboard Jira Decision

## Purpose

Apply one user-approved dashboard failure decision to Jira with the standard dashboard bug fields and evidence format.

## Use When

- A dashboard failure triage workflow has an approved decision for one finding.
- The decision is `new`, `update`, `reopen`, `merge`, or `skip`.
- The task must create or modify an `MPT` Jira bug using dashboard evidence.
- The task must add operation id and stack/message evidence to a Jira description or comment.

## Do Not Use When

- The user has not approved the dashboard finding decision.
- The task is still collecting App Insights data, matching candidate Jira issues, or preparing the batch review table.
- The Jira operation is unrelated to dashboard failure triage.
- The request is only to inspect or explain a Jira issue.

## Inputs

- Approved dashboard finding:
  - generated failure title
  - `cloud_RoleName`
  - `failures_count`
  - operation id or sample operation ids
  - `any_message`, `message`, or stack trace
  - optional order ids, agreement ids, dependency names, dependency URLs, and custom dimensions
- Approved decision:
  - `new`
  - `update <issue-key>`
  - `reopen <issue-key>`
  - `merge <issue-key>`
  - `skip <reason>`
- Jira project key, defaulting to `MPT`.
- Component selected by the workflow or user.
- Dashboard policy fields:
  - `fixVersions`: `v6` and `hotfix`
  - `Environment`: `prod`
  - `Keywords`: include `dashboard`
  - `HitCount`: finding `failures_count`

## Shared References

The path below is relative to the installed package root `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current`. If that root is unavailable while editing this source repository, use the same path under the repository root.

- `skills/mpt-ext-tool-jira-workitem-ops/SKILL.md`

## Bundled Resources

- `scripts/render_dashboard_adf.py`
  - Renders Jira ADF for dashboard evidence.
  - Use it for new issue descriptions and update/reopen/merge comments.

## Workflow

1. Validate the approved decision.
- Stop if the decision is missing, ambiguous, or not approved by the user.
- Stop if `new` is missing a component.
- Stop if `update`, `reopen`, or `merge` is missing a target Jira key.
- For `skip`, do not write Jira; return the skipped finding and reason.

2. Build dashboard evidence.
- Include operation id or sample operation ids.
- Include order ids, agreement ids, dependency names, dependency URLs, and custom dimensions when present.
- Preserve full `any_message`, `message`, or stack trace.
- Use `scripts/render_dashboard_adf.py` to render Jira ADF with an expand and code block.

3. Read target Jira when needed.
- Use `mpt-ext-tool-jira-workitem-ops` for Jira reads and writes.
- For `update`, `reopen`, and `merge`, read the target issue first.
- Capture status, components, fixVersions, Environment, Keywords, and current HitCount.
- If the target is assigned to someone else, follow the assignee safety rule from `mpt-ext-tool-jira-workitem-ops`.

4. Apply the decision.
- For `new`, create an `MPT` Bug with:
  - generated summary
  - component
  - fixVersions `v6` and `hotfix`
  - Environment `prod`
  - Keywords including `dashboard`
  - HitCount set to `failures_count`
  - dashboard evidence as description
- For `update`, add dashboard evidence as a comment and increment current HitCount by `failures_count`.
- For `reopen`, add dashboard evidence as a comment, set HitCount to `failures_count` unless the user explicitly approved accumulation, ensure dashboard policy fields are present, and transition through an explicit available reopen transition.
- For `merge`, add dashboard evidence as a comment to the target issue and update HitCount according to the target issue's approved action semantics.

5. Verify the write.
- Read the issue after create, update, reopen, or merge.
- Verify status, component, fixVersions, Environment, Keywords, HitCount, and dashboard evidence.
- If Jira rejects a field or transition, stop and report the exact blocker.

6. Return the result.
- Return action, Jira link, title, status, components, HitCount, and notes.
- For skipped findings, return the reason and no Jira link.

## Guardrails

- Never apply a decision before user approval.
- Never create a Jira issue for `update`, `reopen`, `merge`, or `skip`.
- Never reopen a rejected duplicate unless the approved decision explicitly targets the canonical issue or explicitly confirms reopening the rejected issue.
- Do not edit Jira status directly; use an explicit workflow transition.
- Do not drop stack traces or truncate Jira evidence payloads.
- Do not guess components when the workflow marked the component as ambiguous.

## Expected Outcome

Exactly one approved dashboard finding decision is applied to Jira, or explicitly skipped, with dashboard evidence and policy fields handled consistently.
