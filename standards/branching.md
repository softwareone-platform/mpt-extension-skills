# Branching Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - work branches in repositories for extensions, tools, and libraries

## Purpose

Define a shared convention for work branch names, base-branch selection, hotfix and backport handling, and push behaviour, so branch creation is consistent across repositories and agents.

## Branch Naming

Use the pattern:

```text
<branch-type>/<JIRA-ID>/<short-description>
```

1. `branch-type` is one of `feature`, `bugfix`, `hotfix`, or `backport`.
2. `JIRA-ID` is the issue key in upper case, for example `MPT-1234`.
3. `short-description` is a lower-case, hyphen-separated slug derived from the Jira issue title (falling back to the description), with filler words removed.

Examples:

```text
feature/MPT-1234/add-property-validation
bugfix/MPT-2345/fix-null-account-id
hotfix/MPT-3456/patch-token-refresh
backport/MPT-4567/backport-token-refresh
```

## Base Branch Selection

1. `feature` and `bugfix` branches are created from `main`.
2. `hotfix` and `backport` branches are created from the active release branch — the `release/*` branch with the highest release number (see [pull-requests.md](./pull-requests.md) for the release-branch definition).
3. If a `hotfix` or `backport` is requested but no `release/*` branch exists, stop and report the blocker instead of inventing a release branch.

## Hotfix and Backport Rules

1. For hotfixes and backports, open the pull request against `main` first, then create the corresponding pull request against the release branch.
2. Use the `[HF]` and `[BACKPORT]` title markers only for pull requests opened against release branches, as defined in [pull-requests.md](./pull-requests.md).

## Push Conventions

1. Keep branch history linear; when updating a branch with the latest changes from its base, rebase instead of creating a merge commit.
2. Prefer a single commit per pull request; amend the existing commit for follow-up changes rather than stacking fix-up commits.
3. When re-pushing an amended or rebased branch that is already published, use `git push --force-with-lease`. Never use a bare `git push --force`, which can clobber concurrent remote commits.

## Related Documents

- [pull-requests.md](./pull-requests.md)
- [commit-messages.md](./commit-messages.md)
