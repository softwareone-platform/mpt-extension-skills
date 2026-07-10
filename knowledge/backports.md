# Backports

Backport policy is defined in [standards/pull-requests.md](../standards/pull-requests.md): the active release branch, main-first ordering, and the `[HF]`/`[BACKPORT]` title markers all come from there. This document covers the operational workflow, with one rule worth restating because it governs every step below: release-branch hotfixes and backports cherry-pick the source pull request commits one by one.

## Hotfix Or Backport Classification

Use the Jira issue type to classify release-branch work:

- `Bug` issues are hotfixes.
- All other issue types are backports.

Before preparing the release pull request, verify that the Jira issue has a fix version that matches the release workflow:

- hotfix work must have a fix version whose name contains `hotfix`
- backport work must have a fix version whose name contains `backport`

If the matching fix version is missing, ask the user whether it should be added before editing Jira.

## Backport Workflow

Hotfixes and backports are always done from `main` to a release branch.

To create a release-branch hotfix or backport:

1. Find the open or merged `main` pull request for the Jira issue, or use the explicit pull request provided by the user.
2. Verify the Jira fix version contains the matching `hotfix` or `backport` marker.
3. Identify the target release branch.
4. Create a new branch from the release branch using the correct `hotfix-` or `backport-` prefix.
5. Cherry-pick the commits from the `main` pull request into the new release work branch one by one, preserving their order.
6. Resolve conflicts if needed.
7. Run the required checks and tests.
8. Open a pull request from the release work branch to the release branch.

## Important limitations

- Do not merge `main` into the release branch as part of the backport flow.
- Do not cherry-pick an arbitrary local branch. Use commits from the open or merged source pull request that targets `main`.
- Cherry-pick source pull request commits one by one, preserving their order.
- If the cherry-pick requires manual conflict resolution, keep the release branch behavior equivalent to the original fix.
