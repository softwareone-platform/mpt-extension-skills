# AGENTS.md

## Purpose

This repository contains shared materials for both humans and AI agents:

- reusable agent skills
- shared engineering standards
- reusable repository documentation guidance
- reusable operational knowledge

An agent should determine whether the task is primarily about a skill, a shared standard, or repository-level documentation guidance before loading more files.

## Repository Layout

- [README.md](./README.md): top-level index for the repository, including links to standards, knowledge, and skills
- `standards/`: shared engineering standards, practices, and reusable cross-repository knowledge
- `knowledge/`: shared operational guidance and reusable how-to documentation
- `docs/`: repository-specific documentation such as installation, distribution, contributing, testing, and documentation guidance
- `skills/*/SKILL.md`: skill definitions for reusable agent workflows

## How To Read This Repository

1. Start with [README.md](./README.md) to understand the repository purpose and the role of `standards/`.
2. Decide whether the user request is primarily about:
   - using or editing a skill
   - applying or updating a shared standard
   - applying or updating shared operational knowledge
   - both
3. If the task is about a specific skill, read only the relevant `SKILL.md` file first.
4. If the task depends on engineering conventions, read the relevant file from `standards/`.
5. If the task is about a reusable workflow or how-to process, read the relevant file from `knowledge/` or `docs/`, depending on where that workflow is documented.
6. If the task is about validating this repository or understanding its test commands, read `docs/testing.md`.
7. If the task is about how to contribute changes in this repository, read `docs/contributing.md`.
8. If the task is about repository documentation validation or documentation structure in this repository, read `docs/documentation.md`.
9. Do not load the entire repository by default. Read only the files needed for the current task.

## How To Use `standards/`

The `standards/` directory is not limited to skills. It is a shared reference for humans and AI agents across multiple repositories.

Use `standards/` when the task involves:

- repository documentation structure
- coding conventions
- testing expectations
- dependency management rules
- build and `Makefile` conventions
- pull request workflow
- extension architecture guidance
- other shared SDLC or engineering practices added later

Treat the files in `standards/` as reusable guidance. If a repository-specific instruction conflicts with a shared standard, prefer the repository-specific instruction and call out the conflict explicitly.

## How To Use `knowledge/`

The `knowledge/` directory contains reusable operational guidance and common how-to workflows that may apply across multiple repositories.

Use `knowledge/` when the task involves:

- building and validating a repository
- understanding common `make` targets
- managing dependencies through shared `uv` workflows
- running checks and tests
- preparing a repository for commit-time validation such as `pre-commit`
- working with migrations
- performing a backport
- understanding repeatable engineering workflows that are not strict standards

Treat `knowledge/` as reusable guidance. Repository-specific commands and exceptions must still come from the target repository documentation.

## Current Standards

- [commit-messages.md](./standards/commit-messages.md): shared commit message format with tag, Jira ID, short summary, and descriptive commit body guidance
- [documentation.md](./standards/documentation.md): repository documentation structure and authoring guidance
- [extensions-best-practices.md](./standards/extensions-best-practices.md): extension architecture and local development guidance
- [makefiles.md](./standards/makefiles.md): shared `Makefile` conventions
- [packages-and-dependencies.md](./standards/packages-and-dependencies.md): Python dependency management rules
- [pull-requests.md](./standards/pull-requests.md): pull request workflow and history rules
- [python-coding.md](./standards/python-coding.md): Python coding conventions
- [skills.md](./standards/skills.md): shared rules and best practices for writing reusable skills
- [unittests.md](./standards/unittests.md): Python unit testing guidelines

## Current Knowledge

- [make-targets.md](./knowledge/make-targets.md): shared reference for common `make` target meanings
- [manage-dependencies.md](./knowledge/manage-dependencies.md): shared dependency-management workflow for repositories that use `uv`
- [build-and-checks.md](./knowledge/build-and-checks.md): shared build and validation workflow guidance
- [migrations.md](./knowledge/migrations.md): shared migration workflow guidance
- [backports.md](./knowledge/backports.md): shared backport workflow guidance

## Repository Docs

- [contributing.md](./docs/contributing.md): repository-specific contribution workflow and links to shared standards
- [documentation.md](./docs/documentation.md): repository-specific documentation validation rules and local linking requirements
- [installation.md](./docs/installation.md): how to install and use the shared skills package from this repository
- [testing.md](./docs/testing.md): repository-specific test and validation commands

## Current Skills

- [mpt-ext-tool-gh-pr-ops](./skills/mpt-ext-tool-gh-pr-ops/SKILL.md): GitHub pull request operations for reading, creating, updating, and replying to PR comments
- [mpt-ext-tool-git-branch-ops](./skills/mpt-ext-tool-git-branch-ops/SKILL.md): Git branch operations for selecting a base branch and creating a safe work branch
- [mpt-ext-tool-jira-workitem-ops](./skills/mpt-ext-tool-jira-workitem-ops/SKILL.md): Jira work item operations for reading, editing, commenting, assignment, and links
- [mpt-ext-task-start-jira-work](./skills/mpt-ext-task-start-jira-work/SKILL.md): Task for moving a Jira issue and its parent chain into In Progress and resolving sprint or assignee mismatches
- [mpt-ext-task-commit-changes](./skills/mpt-ext-task-commit-changes/SKILL.md): Task for staging intended files and creating a repository-compliant commit
- [mpt-ext-task-create-work-branch](./skills/mpt-ext-task-create-work-branch/SKILL.md): Task for reading Jira context and creating a correctly named work branch
- [mpt-ext-task-run-repository-checks](./skills/mpt-ext-task-run-repository-checks/SKILL.md): Task for running the repository-defined local validation flow for current changes
- [mpt-ext-task-fix-repository-check-failures](./skills/mpt-ext-task-fix-repository-check-failures/SKILL.md): Task for fixing failing repository checks and tests one blocker at a time
- [mpt-ext-task-fix-pre-commit-failures](./skills/mpt-ext-task-fix-pre-commit-failures/SKILL.md): Task for resolving failed pre-commit hooks triggered during git commit
- [mpt-ext-task-open-pull-request](./skills/mpt-ext-task-open-pull-request/SKILL.md): Task for opening or updating a repository-compliant pull request
- [mpt-ext-task-move-jira-to-code-review](./skills/mpt-ext-task-move-jira-to-code-review/SKILL.md): Task for transitioning a ready Jira issue into Code Review
- [mpt-ext-task-handle-pr-comments](./skills/mpt-ext-task-handle-pr-comments/SKILL.md): Task for reading PR review feedback, applying scoped fixes, and replying in review threads
- [mpt-ext-task-move-jira-to-qa](./skills/mpt-ext-task-move-jira-to-qa/SKILL.md): Task for transitioning a merged Jira issue into its correct post-merge status
- [mpt-ext-workflow-start-work](./skills/mpt-ext-workflow-start-work/SKILL.md): Workflow for coordinating branch creation and Jira start-state setup
- [mpt-ext-workflow-send-to-review](./skills/mpt-ext-workflow-send-to-review/SKILL.md): Workflow for validating changes, creating or updating the PR, and moving Jira into Code Review
- [mpt-ext-workflow-address-review-feedback](./skills/mpt-ext-workflow-address-review-feedback/SKILL.md): Workflow for processing review comments, validating the resulting changes, and updating the review branch
- [mpt-ext-workflow-complete-after-merge](./skills/mpt-ext-workflow-complete-after-merge/SKILL.md): Workflow for confirming merge completion and moving Jira into its correct post-merge status
- [mpt-ext-workflow-skill-authoring](./skills/mpt-ext-workflow-skill-authoring/SKILL.md): Skill authoring workflow for creating or updating reusable shared skills

## Agent Expectations

- Prefer loading the smallest useful context first.
- Use `standards/` as the source of truth for shared rules.
- Use `knowledge/` for reusable how-to guidance and operational workflows.
- Do not duplicate shared standards into repo-specific documentation unless the task is explicitly about creating a local exception.
- Do not treat `knowledge/` as repository-specific truth when the target repository documents a different command or workflow.
- When updating repository docs in other repositories, prefer linking to shared standards from this repository.
