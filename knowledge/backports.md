# Backports

## Purpose

Describe the shared workflow for carrying hotfixes and backports from `main` to a release branch.

## When To Use This Document

Use this document when you need to:

- backport a change from an open or merged `main` pull request to a release branch
- prepare a hotfix release branch pull request for a Jira bug
- prepare a backport branch and pull request

## General Approach

Backport policy is defined by shared standards. This document describes the operational workflow for carrying it out.

According to the shared pull request rules:

- the active release branch is the `release/*` branch with the highest release number
- hotfixes and backports should be opened for `main` first and only then for the active release branch
- release branch pull requests should preferably use `[HF]` or `[BACKPORT]` markers in the title
- release-branch hotfixes and backports cherry-pick the source pull request commits one by one

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

## Typical Commands

Example Git workflow:

```bash
git fetch origin
git checkout main
git pull --rebase origin main
git checkout release/5
git pull --rebase origin release/5
git checkout -b backport-mpt-1234-fix
git cherry-pick <first_pr_commit_sha>
git cherry-pick <second_pr_commit_sha>
```

## What To Verify

Before opening the backport pull request, verify that:

- the source pull request targets `main`
- the source pull request is open or merged
- the source commit list was read from the source pull request
- the Jira issue has a fix version matching `hotfix` or `backport`, or the user confirmed adding it
- the release work branch was created from the release branch
- the release work branch name uses the correct `hotfix-` or `backport-` prefix
- the release branch still passes the required checks and tests after the cherry-pick

## Important limitations

- Do not merge `main` into the release branch as part of the backport flow.
- Do not cherry-pick an arbitrary local branch. Use commits from the open or merged source pull request that targets `main`.
- Cherry-pick source pull request commits one by one, preserving their order.
- If the cherry-pick requires manual conflict resolution, keep the release branch behavior equivalent to the original fix.

## Related Documents

- [standards/pull-requests.md](../standards/pull-requests.md)
- [knowledge/build-and-checks.md](./build-and-checks.md)
