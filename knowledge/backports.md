# Backports

## Purpose

Describe the shared workflow for backporting changes from `main` to a release branch.

## When To Use This Document

Use this document when you need to:

- backport a merged change from `main` to a release branch
- prepare a backport branch and pull request

## General Approach

Backport policy is defined by shared standards. This document describes the operational workflow for carrying it out.

According to the shared pull request rules:

- the active release branch is the `release/*` branch with the highest release number
- hotfixes and backports should be opened for `main` first and only then for the active release branch
- release branch pull requests should preferably use `[HF]` or `[BACKPORT]` markers in the title
- this workflow assumes pull requests are merged with a merge commit; squash merges are not used for backports

## Backport Workflow

Backports are always done from `main` to a release branch.

To create a backport:

1. Find the merge commit of the original pull request in `main`.
2. Identify the target release branch.
3. Create a new branch from the release branch using the `backport-` prefix.
4. Cherry-pick the merge commit into the new backport branch.
5. Resolve conflicts if needed.
6. Run the required checks and tests.
7. Open a pull request from the backport branch to the release branch.

## Typical Commands

Example Git workflow:

```bash
git fetch origin
git checkout main
git pull --rebase origin main
git log --oneline --merges
git checkout release/5
git pull --rebase origin release/5
git checkout -b backport-mpt-1234-fix
git cherry-pick <merge_commit_sha>
```

## What To Verify

Before opening the backport pull request, verify that:

- the original pull request was merged to `main`
- the correct merge commit from `main` was selected
- the backport branch was created from the release branch
- the backport branch name uses the `backport-` prefix
- the release branch still passes the required checks and tests after the cherry-pick

## Important limitations

- Do not merge `main` into the release branch as part of the backport flow.
- Use the merge commit of the original pull request from `main`.
- If the cherry-pick requires manual conflict resolution, keep the release branch behavior equivalent to the original fix.

## Related Documents

- [standards/pull-requests.md](../standards/pull-requests.md)
- [knowledge/build-and-checks.md](./build-and-checks.md)
