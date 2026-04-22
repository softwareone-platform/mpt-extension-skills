# mpt-extension-skills

Custom AI agent skills, shared engineering standards, and reusable practices for MPT extensions and related repositories.

## Skills in this repository

The [skills/](./skills/) directory contains reusable agent skills.

Current skills:

- [mpt-ext-tool-gh-pr-ops](./skills/mpt-ext-tool-gh-pr-ops/SKILL.md): GitHub pull request operations for create, update, inspection, and comments
- [mpt-ext-tool-git-branch-ops](./skills/mpt-ext-tool-git-branch-ops/SKILL.md): Git branch creation and branch-base selection workflow for starting work safely
- [mpt-ext-tool-jira-workitem-ops](./skills/mpt-ext-tool-jira-workitem-ops/SKILL.md): Jira work item operations for reading, editing, commenting, assignment, and links
- [mpt-ext-task-start-jira-work](./skills/mpt-ext-task-start-jira-work/SKILL.md): Move Jira issues and parent chain into active development state
- [mpt-ext-task-commit-changes](./skills/mpt-ext-task-commit-changes/SKILL.md): Stage intended files and create a repository-compliant commit
- [mpt-ext-task-create-work-branch](./skills/mpt-ext-task-create-work-branch/SKILL.md): Create a work branch from Jira issue context and branch type
- [mpt-ext-task-run-repository-checks](./skills/mpt-ext-task-run-repository-checks/SKILL.md): Run the repository-required local validation flow for the current change scope
- [mpt-ext-task-fix-repository-check-failures](./skills/mpt-ext-task-fix-repository-check-failures/SKILL.md): Work through failing local checks and tests one blocker at a time
- [mpt-ext-task-fix-pre-commit-failures](./skills/mpt-ext-task-fix-pre-commit-failures/SKILL.md): Resolve commit-time pre-commit hook failures one blocker at a time
- [mpt-ext-task-open-pull-request](./skills/mpt-ext-task-open-pull-request/SKILL.md): Create or update a repository-compliant pull request
- [mpt-ext-task-move-jira-to-code-review](./skills/mpt-ext-task-move-jira-to-code-review/SKILL.md): Move a Jira issue into Code Review when branch work is ready for review
- [mpt-ext-task-handle-pr-comments](./skills/mpt-ext-task-handle-pr-comments/SKILL.md): Address existing PR review comments with scoped fixes or thread replies
- [mpt-ext-task-move-jira-to-qa](./skills/mpt-ext-task-move-jira-to-qa/SKILL.md): Move a Jira issue into QA after reviewed work is merged
- [mpt-ext-workflow-start-work](./skills/mpt-ext-workflow-start-work/SKILL.md): Coordinate branch creation and Jira start-of-work setup
- [mpt-ext-workflow-finish-work](./skills/mpt-ext-workflow-finish-work/SKILL.md): Coordinate commit, PR, review feedback handling, and Jira completion states
- [mpt-ext-workflow-skill-authoring](./skills/mpt-ext-workflow-skill-authoring/SKILL.md): Shared workflow skill for creating and updating reusable skills

For installation and package usage, see [docs/installation.md](./docs/installation.md).

## Shared Standards

The [standards/](./standards/) directory contains shared standards and engineering policies that can be referenced from multiple repositories.

It is not limited to skills-related guidance. The `standards/` directory is intended to be a shared reference point for:

- repository-level engineering standards
- shared development and SDLC practices
- conventions that should stay consistent across extensions, tools, and libraries
- reference material that can be consumed by both humans and AI agents

Use `standards/` for documents that define reusable expectations, policies, and shared engineering rules across repositories.

Examples:

- coding standards and testing rules
- dependency and build conventions
- SDLC practices such as pull request, review, and release expectations
- architectural or operational guidance that should remain stable across projects

Avoid using this directory for:

- repository-specific implementation notes
- temporary decisions or draft discussions
- one-off instructions that belong in a single repository README or ADR

Current documents in `standards/`:

- [commit-messages.md](./standards/commit-messages.md): shared commit message format with tag, Jira ID, short summary, and required AI-generated description line
- [documentation.md](./standards/documentation.md): shared repository documentation structure and authoring rules for human readers and AI agents
- [extensions-best-practices.md](./standards/extensions-best-practices.md): extension architecture and design guidance for isolation, deployability, local development, and reusability
- [makefiles.md](./standards/makefiles.md): shared `Makefile` structure and expectations for organizing common development commands
- [packages-and-dependencies.md](./standards/packages-and-dependencies.md): shared dependency management rules for Python repositories, including `uv`, lock files, and version pinning strategy
- [pull-requests.md](./standards/pull-requests.md): shared pull request rules for titles, commit structure, reviewability, testing, and release branch workflows
- [python-coding.md](./standards/python-coding.md): shared Python coding conventions, including typing, docstrings, linting, and naming expectations
- [skills.md](./standards/skills.md): shared rules and best practices for writing reusable skills
- [unittests.md](./standards/unittests.md): Python unit testing guidelines, including test structure, parametrization, determinism, and mocking rules

These standards are intended to be linked from repository-level documentation rather than copied into each repository.

## Shared Knowledge

The [knowledge/](./knowledge/) directory contains reusable how-to documentation and operational guidance that can be referenced from multiple repositories.

Use `knowledge/` for documents that explain shared workflows or repeatable tasks without turning them into normative standards.

Examples:

- how to build and validate a repository
- how to use common `make` targets
- how to manage dependencies through the shared `uv` workflow
- how to run or create migrations
- how to perform a backport
- how to execute common development workflows across repositories

Current documents in `knowledge/`:

- [make-targets.md](./knowledge/make-targets.md): shared reference for common `make` targets and their typical meaning
- [manage-dependencies.md](./knowledge/manage-dependencies.md): shared dependency-management workflow for repositories that use `uv`
- [build-and-checks.md](./knowledge/build-and-checks.md): shared guidance for building repositories and validating that checks and tests pass
- [migrations.md](./knowledge/migrations.md): shared workflow for running, checking, and creating migrations
- [backports.md](./knowledge/backports.md): shared workflow for backporting changes to the active release branch

Repository docs in `docs/`:

- [contributing.md](./docs/contributing.md): repository-specific contribution workflow and links to shared standards
- [documentation.md](./docs/documentation.md): repository-specific documentation validation rules and local linking requirements
- [installation.md](./docs/installation.md): how to install and use the shared skills package from this repository
- [testing.md](./docs/testing.md): how to run shell validation and integration tests for this repository
