# Testing

## Purpose

Describe the repository-specific validation workflow for shell scripts, local checks, and CI behavior.

## Validation Scope

This repository currently validates:

- shell script quality with `shellcheck`
- shell script behavior with repository integration tests

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
shellcheck scripts/mpt-skills.sh
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
make check-all
```

Current commands:

- `make check`: runs `shellcheck`
- `make test`: runs the shell integration tests
- `make check-all`: runs both validation and tests

Use `make help` to see the available commands.

## CI Validation

GitHub Actions runs the shell validation workflow on:

- pull requests
- pushes to `main`

The workflow runs:

- `shellcheck 0.11.0` for `scripts/mpt-skills.sh`
- `bash tests/test_mpt_skills.sh`

## Related Documents

- [contributing.md](./contributing.md)
- [installation.md](./installation.md)
- [../Makefile](../Makefile)
- [../make/repo.mk](../make/repo.mk)
- [../scripts/mpt-skills.sh](../scripts/mpt-skills.sh)
- [../tests/test_mpt_skills.sh](../tests/test_mpt_skills.sh)
- [../README.md](../README.md)
