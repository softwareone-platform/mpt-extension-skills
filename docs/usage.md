# Usage

## Purpose

Describe the installed CLI commands for managing shared skills after first-time installation.

## Installed Command

Use:

```bash
mpt-extensions-skills
```

## What Gets Installed

The release package and local installer install:

- `bin/`
- `skills/`
- `standards/`
- `knowledge/`
- `docs/`
- `manifest.json`

## Runtime Selection

By default, install, upgrade, activate, and deactivate auto-detect available runtimes.

Use explicit runtime flags when needed:

```bash
mpt-extensions-skills install --version 1.0.0 --codex
mpt-extensions-skills install --version 1.0.0 --claude
mpt-extensions-skills install --version 1.0.0 --all
mpt-extensions-skills install --version 1.0.0 --cursor=/path/to/repo
```

Supported runtime flags:

- `--codex`
- `--claude`
- `--all`
- `--cursor[=<dir>]` — copy the Cursor rule adapter into `<dir>/.cursor/rules`
  (default: current directory). Explicit only: never auto-detected and not
  included by `--all`; combine it with `--codex`/`--claude` as needed, and
  remove a project's adapter with `deactivate --cursor=<dir>`. The directory can
  also be set with the `CURSOR_PROJECT_DIR` environment variable.

## Environment Variables

The CLI supports these environment variable overrides:

- `MPT_EXTENSION_SKILLS_HOME`: root directory for installed package versions and the `current` symlink. Default: `~/.mpt-extension-skills`
- `CODEX_SKILLS_DIR`: Codex skills directory that receives managed shared skill links during activation. Default: `~/.codex/skills`
- `CLAUDE_SKILLS_DIR`: Claude skills directory that receives managed shared skill links during activation. Default: `~/.claude/skills`
- `MPT_SKILLS_BIN_DIR`: directory where the user-facing `mpt-extensions-skills` command is linked. Default: `~/.local/bin`
- `CURSOR_PROJECT_DIR`: project directory whose `.cursor/rules` receives the Cursor adapter when `--cursor` is given without a value. Default: current directory

## Install A Specific Release

After first-time installation, install a specific GitHub release through the CLI:

```bash
mpt-extensions-skills install --version 1.0.0
```

## Upgrade

Upgrade to the latest GitHub release:

```bash
mpt-extensions-skills upgrade
```

Install and activate a specific GitHub release:

```bash
mpt-extensions-skills upgrade --version 1.0.0
```

## Local Debug Installation

Install from a local repository checkout as the special `local` version:

```bash
mpt-extensions-skills install --path /path/to/mpt-extension-skills
```

The `local` version replaces any previous local installation and becomes the active `current` target.

From this repository checkout, the same local installation is available through `make`:

```bash
make install-skills
make install-skills runtime="--codex"
make install-skills runtime="--all"
```

To upgrade an installed package from GitHub Releases through `make`, use:

```bash
make update-skills
make update-skills version=1.0.0
make update-skills runtime="--codex"
```

## Show Installed Version

Use:

```bash
mpt-extensions-skills --help
```

The help output shows the currently active installed version.

## List Installed Versions

Use:

```bash
mpt-extensions-skills list
```

The active version is marked in the installed versions output.
The latest 10 GitHub releases that can be installed are listed separately:

```text
Installed versions:
  1.10.0
  1.1.0 (active)
  1.0.0
  local
Available GitHub releases:
  1.10.0
  1.3.0
  1.2.0
```

## Activate A Previously Installed Version

Use:

```bash
mpt-extensions-skills activate 1.0.0
```

Examples with explicit runtime selection:

```bash
mpt-extensions-skills activate 1.0.0 --codex
mpt-extensions-skills activate 1.0.0 --claude
mpt-extensions-skills activate 1.0.0 --all
```

## Deactivate Runtime Links

Use:

```bash
mpt-extensions-skills deactivate
```

`deactivate` removes only managed skill links from selected runtime directories
(and, with `--cursor`, the rule adapter from the target project's
`.cursor/rules`). It does not delete installed versions from
`~/.mpt-extension-skills`.

Examples with explicit runtime selection:

```bash
mpt-extensions-skills deactivate --codex
mpt-extensions-skills deactivate --claude
mpt-extensions-skills deactivate --all
mpt-extensions-skills deactivate --cursor=/path/to/repo
```

## Remove Everything

Use:

```bash
mpt-extensions-skills remove --all
```

This command:

- removes managed skill links from detected Codex and Claude runtime directories
- removes the user command link from `~/.local/bin` or `MPT_SKILLS_BIN_DIR`
- removes the package install root such as `~/.mpt-extension-skills`

Cursor adapters live inside individual project trees, so `remove --all` does not
touch them. Remove a project's adapter with `deactivate --cursor=<dir>`.

## Release Workflow

Repository maintainers publish a release manually from the GitHub Actions `Release` workflow.
The workflow accepts a version without a `v` prefix, creates an annotated Git tag with the same value, and creates the GitHub release title as `v<version>`.
The GitHub release body is generated automatically with GitHub release notes.

Each release publishes:

- `mpt-extensions-skills-install.sh`
- `mpt-extension-skills-<version>.tar.gz`
- `SHA256SUMS`

## Related Documents

- [installation.md](./installation.md)
- [testing.md](./testing.md)
- [../scripts/mpt-extensions-skills.sh](../scripts/mpt-extensions-skills.sh)
