# Architecture

This repository is a content repository, not a deployable service. It holds the
shared materials consumed by humans and AI agents across MPT extensions, tools,
and libraries: reusable skills, engineering standards, operational knowledge,
repository docs, and the supporting CLI and configuration.

## Top-level structure

```text
skills/                 reusable agent skills (one directory per skill)
standards/              shared engineering standards (normative)
knowledge/              reusable operational how-to (non-normative)
docs/                   documentation specific to this repository
scripts/                install/upgrade CLI and the token-budget checker
make/                   repository make targets
tests/                  shell tests for the CLI
.claude-plugin/         Claude Code plugin manifest and marketplace catalog
.codex-plugin/          Codex plugin manifest
.cursor/rules/          Cursor rule adapter (instruction-tier)
.github/workflows/      release-prepare (stamp + PR) and release (tag + publish)
coderabbit-shared.yaml  shared CodeRabbit config inherited by consuming repos
Makefile                entry point that includes make/*.mk
```

## Components and responsibilities

- **`skills/`** — the core deliverable. Each skill is a directory named
  `mpt-ext-<type>-<short-purpose>/` containing a `SKILL.md` entry point, a
  required `agents/openai.yaml` cross-runtime adapter, and optional `scripts/`
  for deterministic logic. Skills are classified as `tool`, `task`, or
  `workflow`. Authoring rules and the naming/structure contract live in
  [standards/skills.md](../standards/skills.md).
- **`standards/`** — normative, reusable engineering rules (documentation,
  commit messages, pull requests, Python coding, testing, makefiles,
  dependencies, extension best practices, skills). Repositories link to these
  rather than copying them.
- **`knowledge/`** — reusable how-to and operational guidance (build and checks,
  make targets, dependency management, migrations, backports). Non-normative:
  the target repository's own commands take precedence when they differ.
- **`docs/`** — documentation about *this* repository (installation, usage,
  contributing, testing, the documentation rules, and this architecture). It
  follows [standards/documentation.md](../standards/documentation.md).
- **`scripts/`** — `mpt-extensions-skills.sh` / `mpt-extensions-skills-install.sh`
  (install and upgrade skills into a runtime) and `skill_token_budget.py` (token
  budgets for skill descriptions and adapters).
- **`make/`** — repository targets (`check`, `test`, `token-budget`,
  `token-budget-check`, `check-all`, install/update). See
  [docs/contributing.md](contributing.md) and the shared
  [knowledge/make-targets.md](../knowledge/make-targets.md).
- **`coderabbit-shared.yaml`** — the shared CodeRabbit review configuration that
  consuming repositories inherit, including the cross-repo review path
  instructions and pre-merge checks.

## Boundaries

- **Standards vs knowledge vs docs**: `standards/` defines rules that should stay
  consistent across repos; `knowledge/` explains repeatable workflows; `docs/`
  describes only this repository. A skill links to `standards/` and `knowledge/`
  instead of duplicating them.
- **Skill types**: a `tool` skill wraps one integration, a `task` skill performs
  one bounded job, and a `workflow` skill coordinates task-level steps. A
  workflow may orchestrate tasks; a tool never orchestrates other skills.
- **Authoring vs runtime**: `SKILL.md` is the behaviour document; `agents/openai.yaml`
  is the adapter loaded by Codex/OpenAI-style runtimes.

## Distribution and consumption

Skills are installed into a runtime via the bundled CLI and resolved at runtime
under `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current`. Skills
that need shared guidance read it from `standards/`, `knowledge/`, or `docs/`
under that installed root, falling back to the `main` branch of this repository
when the installed root is unavailable. Installation and upgrade flows are
documented in [docs/installation.md](installation.md) and
[docs/usage.md](usage.md).

The same `skills/` are also published as a plugin for runtimes with a plugin
marketplace. `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` are the
Claude and Codex plugin manifests; `.claude-plugin/marketplace.json` is the
marketplace catalog whose plugin `source` is pinned to the release tag.
`.cursor/rules/mpt-extension-skills.mdc` is the Cursor adapter (instruction-tier,
no marketplace). Releases are two-step: the **Prepare release** workflow stamps
the manifest versions and opens a `release/<version>` pull request; merging it
triggers the **Release** workflow, which tags the version, builds the package
assets, and publishes the GitHub release. The manifest version, the marketplace
version, and the git tag therefore always match.

## Related documentation

- [contributing.md](contributing.md) — contribution workflow and commands
- [testing.md](testing.md) — shell validation and tests
- [documentation.md](documentation.md) — repository documentation rules
- [standards/skills.md](../standards/skills.md) — skill authoring contract
- [standards/documentation.md](../standards/documentation.md) — documentation guideline
