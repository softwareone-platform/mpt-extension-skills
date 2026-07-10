# CLI Command Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - command-line commands exposed by Python extensions, tools, and libraries

## Purpose
Define how command-line commands are implemented and how they must be runnable in containerized environments.

## Definitions

- A `legacy extension` is an extension built on the Django-based MPT extension runtime that already exposes Django management commands.

## General Rules

1. Implement new CLI commands with [`typer`](https://typer.tiangolo.com/).
2. For legacy (Django-based) extensions, implement CLI commands as Django management commands instead of adding a separate CLI framework.
3. Do not hand-roll argument parsing with `argparse` or raw `sys.argv` for new commands when `typer` or Django management commands apply.
4. Every CLI command must be runnable inside the application's Docker container, not only on a developer host.
5. A `typer` CLI must be installed as a named console command (an entry point) so that inside the container it is invoked by its command name, not through a Python module launcher.
 - Register the entry point in `pyproject.toml` under `[project.scripts]` so the command name is on `PATH` inside the image.
 - Inside the container the command must run as `docker compose run --rm app <command> ...` (for example `mpt-extension create extension`), **not** as `python -m <module> ...`.

GOOD
```bash
docker compose run --rm app mpt-extension create extension
```

BAD
```bash
docker compose run --rm app python -m extension.cli create extension
```

6. Django management commands (legacy extensions) are invoked through `manage.py`. Running them as `docker compose run --rm app python manage.py <command> ...` inside the container is the expected and correct form — the named-entry-point rule above applies to `typer` CLIs, not to Django management commands.
7. Commands must not depend on developer-host-only state such as local file paths or host-only environment. Any required configuration must be available inside the container.
8. `--help` must work inside the container, and each command must be documented in the repository docs.
