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
- [mpt-ext-task-dependabot-pr-policy-fix](./skills/mpt-ext-task-dependabot-pr-policy-fix/SKILL.md): Apply dependency-policy fixes to a selected Dependabot PR or checked-out branch
- [mpt-ext-task-run-repository-checks](./skills/mpt-ext-task-run-repository-checks/SKILL.md): Run the repository-required local validation flow for the current change scope
- [mpt-ext-task-fix-repository-check-failures](./skills/mpt-ext-task-fix-repository-check-failures/SKILL.md): Work through failing local checks and tests one blocker at a time
- [mpt-ext-task-fix-pre-commit-failures](./skills/mpt-ext-task-fix-pre-commit-failures/SKILL.md): Resolve commit-time pre-commit hook failures one blocker at a time
- [mpt-ext-task-apply-dashboard-jira-decision](./skills/mpt-ext-task-apply-dashboard-jira-decision/SKILL.md): Apply one approved dashboard failure decision to MPT Jira
- [mpt-ext-task-open-pull-request](./skills/mpt-ext-task-open-pull-request/SKILL.md): Create or update a repository-compliant pull request
- [mpt-ext-task-move-jira-to-code-review](./skills/mpt-ext-task-move-jira-to-code-review/SKILL.md): Move a Jira issue into Code Review when branch work is ready for review
- [mpt-ext-task-handle-pr-comments](./skills/mpt-ext-task-handle-pr-comments/SKILL.md): Address existing PR review comments with scoped fixes or thread replies
- [mpt-ext-task-move-jira-to-qa](./skills/mpt-ext-task-move-jira-to-qa/SKILL.md): Move a Jira issue into its correct post-merge status after reviewed work is merged
- [mpt-ext-task-write-documentation](./skills/mpt-ext-task-write-documentation/SKILL.md): Author or refresh a repository's required documentation set following the documentation guideline
- [mpt-ext-task-update-docs-from-changes](./skills/mpt-ext-task-update-docs-from-changes/SKILL.md): Update repository documentation from a code change set (unstaged, uncommitted, last commit, or branch diff)
- [mpt-ext-task-create-initial-epic](./skills/mpt-ext-task-create-initial-epic/SKILL.md): Create the initial epic plus a 3d "Design, investigate and research" user story at kickoff
- [mpt-ext-workflow-start-work](./skills/mpt-ext-workflow-start-work/SKILL.md): Coordinate branch creation and Jira start-of-work setup
- [mpt-ext-workflow-dashboard-failure-triage](./skills/mpt-ext-workflow-dashboard-failure-triage/SKILL.md): Batch triage App Insights dashboard failures into MPT Jira bugs
- [mpt-ext-workflow-fix-dependabot-prs](./skills/mpt-ext-workflow-fix-dependabot-prs/SKILL.md): Coordinate Dependabot PR discovery, policy fixes, validation, scoped check fixes, amend, and push
- [mpt-ext-workflow-hotfix-backport](./skills/mpt-ext-workflow-hotfix-backport/SKILL.md): Coordinate release-branch hotfix and backport PR preparation
- [mpt-ext-workflow-send-to-review](./skills/mpt-ext-workflow-send-to-review/SKILL.md): Coordinate documentation update, validation, commit, PR creation, and Jira review handoff
- [mpt-ext-workflow-address-review-feedback](./skills/mpt-ext-workflow-address-review-feedback/SKILL.md): Coordinate review comment handling, validation, and updated branch publication
- [mpt-ext-workflow-complete-after-merge](./skills/mpt-ext-workflow-complete-after-merge/SKILL.md): Coordinate merge confirmation and the final Jira post-merge handoff
- [mpt-ext-workflow-skill-authoring](./skills/mpt-ext-workflow-skill-authoring/SKILL.md): Shared workflow skill for creating and updating reusable skills
- [mpt-ext-workflow-update-documentation](./skills/mpt-ext-workflow-update-documentation/SKILL.md): Coordinate updating documentation for a change set: update affected docs, self-check, and stage
- [mpt-ext-workflow-decompose-tdr](./skills/mpt-ext-workflow-decompose-tdr/SKILL.md): Break a TDR or epic into agreed user stories and then estimated Back/Front subtasks

For first-time installation from GitHub Releases, see [docs/installation.md](./docs/installation.md).
For installed CLI commands, updates, local debug installs, and release lifecycle usage, see [docs/usage.md](./docs/usage.md).

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

- [cli.md](./standards/cli.md): shared rules for implementing CLI commands with `typer` or Django management commands and keeping them runnable inside Docker
- [commit-messages.md](./standards/commit-messages.md): shared commit message format with tag, Jira ID, short summary, and descriptive commit body guidance
- [documentation.md](./standards/documentation.md): shared repository documentation structure and authoring rules for human readers and AI agents
- [extensions-best-practices.md](./standards/extensions-best-practices.md): extension architecture and design guidance for isolation, deployability, local development, and reusability
- [makefiles.md](./standards/makefiles.md): shared `Makefile` structure and expectations for organizing common development commands
- [packages-and-dependencies.md](./standards/packages-and-dependencies.md): shared dependency management rules for Python repositories, including `uv`, lock files, and version pinning strategy
- [pull-requests.md](./standards/pull-requests.md): shared pull request rules for titles, commit structure, reviewability, testing, and release branch workflows
- [python-coding.md](./standards/python-coding.md): shared Python coding conventions, including typing, docstrings, linting, and naming expectations
- [skills.md](./standards/skills.md): shared rules and best practices for writing reusable skills
- [unittests.md](./standards/unittests.md): Python unit testing guidelines, including test structure, parametrization, determinism, and mocking rules
- [user-stories.md](./standards/user-stories.md): work breakdown standard for turning an epic or TDR into demoable, estimated user stories and Back/Front subtasks

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

- [architecture.md](./docs/architecture.md): repository structure, the skills/standards/knowledge/docs layout, and how the parts fit together
- [contributing.md](./docs/contributing.md): repository-specific contribution workflow and links to shared standards
- [documentation.md](./docs/documentation.md): repository-specific documentation validation rules and local linking requirements
- [installation.md](./docs/installation.md): first-time installation from GitHub Releases
- [usage.md](./docs/usage.md): installed CLI commands, updates, local debug installs, and release lifecycle usage
- [testing.md](./docs/testing.md): how to run shell validation and integration tests for this repository
