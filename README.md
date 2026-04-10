# mpt-extension-skills

Custom AI agent skills, shared engineering standards, and reusable practices for MPT extensions and related repositories.

## Skills in this repository

The [skills/](./skills/) directory contains reusable agent skills.

Current skills:

- [swo-gh-commit-pr](./skills/swo-gh-commit-pr/SKILL.md): Git commit + GitHub PR workflow skill
- [swo-jira-workitem-ops](./skills/swo-jira-workitem-ops/SKILL.md): Jira work item operations skill

For prerequisites and setup/install examples, see [knowledge/skills_setup.md](./knowledge/skills_setup.md).

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

- [documentation.md](./standards/documentation.md): shared repository documentation structure and authoring rules for human readers and AI agents
- [extensions-best-practices.md](./standards/extensions-best-practices.md): extension architecture and design guidance for isolation, deployability, local development, and reusability
- [makefiles.md](./standards/makefiles.md): shared `Makefile` structure and expectations for organizing common development commands
- [packages-and-dependencies.md](./standards/packages-and-dependencies.md): shared dependency management rules for Python repositories, including `uv`, lock files, and version pinning strategy
- [pull-requests.md](./standards/pull-requests.md): shared pull request rules for titles, commit structure, reviewability, testing, and release branch workflows
- [python-coding.md](./standards/python-coding.md): shared Python coding conventions, including typing, docstrings, linting, and naming expectations
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
- [skills_setup.md](./knowledge/skills_setup.md): shared skill setup and install workflows
