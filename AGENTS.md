# AGENTS.md

## Purpose

This repository contains shared materials for both humans and AI agents:

- reusable agent skills
- shared engineering standards
- reusable repository documentation guidance
- reusable operational knowledge

An agent should determine whether the task is primarily about a skill, a shared standard, or repository-level documentation guidance before loading more files.

## Repository Layout

- `README.md`: top-level description of the repository, its purpose, and the current shared standards
- `standards/`: shared engineering standards, practices, and reusable cross-repository knowledge
- `knowledge/`: shared operational guidance and reusable how-to documentation
- `skills/*/SKILL.md`: skill definitions for reusable agent workflows

## How To Read This Repository

1. Start with `README.md` to understand the repository purpose and the role of `standards/`.
2. Decide whether the user request is primarily about:
   - using or editing a skill
   - applying or updating a shared standard
   - applying or updating shared operational knowledge
   - both
3. If the task is about a specific skill, read only the relevant `SKILL.md` file first.
4. If the task depends on engineering conventions, read the relevant file from `standards/`.
5. If the task is about a reusable workflow or how-to process, read the relevant file from `knowledge/`.
6. Do not load the entire repository by default. Read only the files needed for the current task.

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
- running checks and tests
- working with migrations
- performing a backport
- understanding repeatable engineering workflows that are not strict standards

Treat `knowledge/` as reusable guidance. Repository-specific commands and exceptions must still come from the target repository documentation.

## Current Standards

- `standards/documentation.md`: repository documentation structure and authoring guidance
- `standards/extensions-best-practices.md`: extension architecture and local development guidance
- `standards/makefiles.md`: shared `Makefile` conventions
- `standards/packages-and-dependencies.md`: Python dependency management rules
- `standards/pull-requests.md`: pull request workflow and history rules
- `standards/python-coding.md`: Python coding conventions
- `standards/unittests.md`: Python unit testing guidelines

## Current Knowledge

- `knowledge/make-targets.md`: shared reference for common `make` target meanings
- `knowledge/build-and-checks.md`: shared build and validation workflow guidance
- `knowledge/migrations.md`: shared migration workflow guidance
- `knowledge/backports.md`: shared backport workflow guidance

## Current Skills

- `skills/swo-gh-commit-pr/SKILL.md`: Git commit and GitHub pull request workflow skill
- `skills/swo-jira-workitem-ops/SKILL.md`: Jira work item operations skill

## Agent Expectations

- Prefer loading the smallest useful context first.
- Use `standards/` as the source of truth for shared rules.
- Use `knowledge/` for reusable how-to guidance and operational workflows.
- Do not duplicate shared standards into repo-specific documentation unless the task is explicitly about creating a local exception.
- Do not treat `knowledge/` as repository-specific truth when the target repository documents a different command or workflow.
- When updating repository docs in other repositories, prefer linking to shared standards from this repository.
