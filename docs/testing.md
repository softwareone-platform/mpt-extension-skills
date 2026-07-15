# Testing

## Purpose

Describe the repository-specific validation workflow for shell scripts, local checks, and CI behavior.

## Validation Scope

This repository currently validates:

- shell script quality with `shellcheck`
- shell script behavior with repository integration tests
- skill token budget: the always-on and per-invocation fields of each skill (`SKILL.md` `description`/body and `agents/openai.yaml` `short_description`/`default_prompt`) stay within the limits in [standards/skills.md](../standards/skills.md)

## Install Shellcheck

Use `shellcheck` version `0.11.0`.

Use one of the following local installation methods.

macOS with Homebrew:

```bash
brew install shellcheck
```

Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y shellcheck
```

## Local Validation Workflow

Run shell linting from the repository root:

```bash
shellcheck scripts/mpt-extensions-skills.sh scripts/mpt-extensions-skills-install.sh
```

Run shell tests from the repository root:

```bash
bash tests/test_mpt_skills.sh
```

Use both commands before committing changes to shell scripts or installer behavior.

## Make Commands

This repository exposes the main validation commands through `make`:

```bash
make check
make test
make test-scripts
make token-budget
make token-budget-check
make check-all
make install-skills
make update-skills
make review
```

Current commands:

- `make check`: runs `shellcheck` for the CLI and release installer scripts
- `make test`: runs the shell integration tests
- `make test-scripts`: runs the skill-script `pytest` suite with branch coverage inside Docker via `docker compose run --rm tests` (needs Docker; no host Python packages required)
- `make token-budget`: reports the token footprint of every skill across both runtimes (Claude `SKILL.md` `description`/body and Codex `agents/openai.yaml` `short_description`/`default_prompt`)
- `make token-budget-check`: fails if any gated field exceeds its budget (`description`, `short_description`, or `default_prompt`)
- `make check-all`: runs validation, tests, and the skill token-budget check
- `make install-skills`: installs skills from the local repository checkout
- `make update-skills`: upgrades installed skills from GitHub Releases
- `make review`: runs the local CodeRabbit review command

Use `make help` to see the available commands.

## Skill Script Tests

Skill scripts under `skills/*/scripts/*.py` are covered by `pytest` tests in `tests/scripts/`, run with `make test-scripts` and as part of `make check-all` (so they gate PRs and merges to `main`).

- Test dependencies (`pytest`, `pytest-cov`) are managed with `uv` in the `dev` dependency group of `pyproject.toml` and locked in `uv.lock`. Add or change them with `uv add --dev <pkg>` / `uv lock`.
- Run them with `make test-scripts`, which builds the `tests` service from the repository `Dockerfile` (Python 3.12; `uv sync --frozen --only-group dev` installs the locked dev group) and runs `pytest` in the container via `docker compose`. No host Python packages are needed; the repository is mounted so coverage runs against the current source. To run without Docker instead, use `uv run --group dev pytest`.
- Tests import each script in-process and exercise its `main()` and pure functions, so `pytest-cov` measures real line and branch coverage. Shared helpers (module loader, in-process `main()` runner) live in `tests/scripts/helpers.py`.
- Coverage is configured in `pyproject.toml`: pytest enables it via `[tool.pytest.ini_options] addopts = "--cov --cov-report=term-missing"`; `[tool.coverage.run]` sets `branch = true` and `source = ["skills"]`; `[tool.coverage.report]` restricts it with `include = ["skills/*/scripts/*.py"]` and enforces `fail_under = 95`. Because the coverage source is the scripts directory, a script with no test counts as uncovered and drags the total below the threshold — so adding a new skill script requires adding its tests. This branch-coverage gate replaces the need for a separate coverage-guard module.

## Local CodeRabbit Review

To run CodeRabbit locally, install and authenticate the CodeRabbit CLI first.

The official CLI command uses `cr` as the short alias for `coderabbit`.

From the repository root, run:

```bash
make review
```

This target runs:

```bash
coderabbit review
```

You can pass additional CLI options through `args`:

```bash
make review args="--plain"
make review args="--base release/5"
```

## Skill Token Budget

Skills are consumed by two runtimes, each with an always-on surface (loaded every session, whether or not the skill is used) and a per-invocation surface (loaded only when the skill runs):

- Claude reads `SKILL.md`: the frontmatter `description` is always-on, the body is per-invocation.
- Codex/OpenAI reads `agents/openai.yaml`: `short_description` is always-on, `default_prompt` is per-invocation.

An oversized always-on field is a permanent token cost, so the budget tool measures all four surfaces and guards them.

Report the footprint of every skill:

```bash
make token-budget
```

This prints, per skill, the `description` word count, the `SKILL.md` body size, and the `short_description` and `default_prompt` word counts, plus totals, and flags any field over its limit.

Gate it (used by `make check-all`, and suitable for CI):

```bash
make token-budget-check
```

This exits non-zero when any gated field (`description`, `short_description`, or `default_prompt`) exceeds the limit defined in [standards/skills.md](../standards/skills.md). Run it directly with options through the report target:

```bash
make token-budget args="--check"
```

## CI Validation

GitHub Actions runs the shell validation workflow on:

- pull requests
- pushes to `main`

The workflow runs:

- `shellcheck 0.11.0` (pinned action) over `./scripts`
- `make check-all`, which runs `shellcheck` for `scripts/mpt-extensions-skills.sh` and `scripts/mpt-extensions-skills-install.sh`, `bash tests/test_mpt_skills.sh`, `make test-scripts` (pytest with a 95% branch-coverage gate, run in Docker via `docker compose`), and `make token-budget-check`.

So the skill token-budget gate runs in CI as part of `make check-all`.

Local `make check` uses the `SHELLCHECK` command available on the developer machine.
Install shellcheck `0.11.0` locally when you need parity with CI; otherwise CI remains the authoritative shellcheck version gate for these two scripts.

## Related Documents

- [contributing.md](./contributing.md)
- [installation.md](./installation.md)
- [usage.md](./usage.md)
- [../Makefile](../Makefile)
- [../make/external_tools.mk](../make/external_tools.mk)
- [../make/repo.mk](../make/repo.mk)
- [../scripts/mpt-extensions-skills.sh](../scripts/mpt-extensions-skills.sh)
- [../scripts/mpt-extensions-skills-install.sh](../scripts/mpt-extensions-skills-install.sh)
- [../scripts/skill_token_budget.py](../scripts/skill_token_budget.py)
- [../standards/skills.md](../standards/skills.md)
- [../tests/test_mpt_skills.sh](../tests/test_mpt_skills.sh)
- [../README.md](../README.md)
