# Installation

## Purpose

Describe how to install and use the shared skills package from this repository.

## Prerequisites

- A local agent/tool runtime that supports file-based skills
- Access to your local home directories for Codex or Claude
- Access to a local user bin directory such as `~/.local/bin`

## Install From A Local Clone

From the repository root:

```bash
./scripts/mpt-skills.sh install 1.0.0
```

You can also use the installed command after the first install:

```bash
mpt-skills install 1.0.0
```

## What Gets Installed

The installer installs:

- `bin/`
- `skills/`
- `standards/`
- `knowledge/`
- `docs/`
- `manifest.json`

## Installed Commands

The package installs the CLI into the versioned package and exposes the user-facing command as:

```bash
mpt-skills
```

By default this command is linked into:

```text
~/.local/bin/mpt-skills
```

## Runtime Selection

By default, the installer auto-detects installed runtimes and wires only those.
If Codex and Claude runtime directories are both present, `install` without flags behaves like installing for both runtimes.

You can also target runtimes explicitly:

```bash
./scripts/mpt-skills.sh install 1.0.0 --codex
./scripts/mpt-skills.sh install 1.0.0 --claude
./scripts/mpt-skills.sh install 1.0.0 --all
```

The same runtime flags are supported for `activate`.
The same runtime flags are supported for `deactivate`.
Without flags, `deactivate` also auto-detects the available runtime directories and removes managed links only from the runtimes it finds.
Use `remove --all` when you want to remove the installed package completely.

## Environment Variables

The installer and activation command support these environment variable overrides:

- `MPT_EXTENSION_SKILLS_HOME`: root directory for installed package versions and the `current` symlink. Default: `~/.mpt-extension-skills`
- `CODEX_SKILLS_DIR`: Codex skills directory that receives managed shared skill links during activation. Default: `~/.codex/skills`
- `CLAUDE_SKILLS_DIR`: Claude skills directory that receives managed shared skill links during activation. Default: `~/.claude/skills`
- `MPT_SKILLS_BIN_DIR`: directory where the user-facing `mpt-skills` command is linked. Default: `~/.local/bin`

Example:

```bash
export MPT_EXTENSION_SKILLS_HOME="$HOME/.local/share/mpt-extension-skills"
export CODEX_SKILLS_DIR="$HOME/.codex/skills"
export CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
export MPT_SKILLS_BIN_DIR="$HOME/.local/bin"

./scripts/mpt-skills.sh install 1.0.0 --all
```

Use these overrides when your runtime directories or local bin directory differ from the defaults.

## Show Installed Version

Use:

```bash
mpt-skills --help
```

The help output shows the currently active installed version.

## List Installed Versions

Use:

```bash
mpt-skills list
```

The active version is marked in the output:

```text
1.0.0 (active)
1.1.0
```

## Activate A Previously Installed Version

Use:

```bash
mpt-skills activate 1.0.0
```

Examples with explicit runtime selection:

```bash
mpt-skills activate 1.0.0 --codex
mpt-skills activate 1.0.0 --claude
mpt-skills activate 1.0.0 --all
```

## Deactivate Runtime Links

Use:

```bash
mpt-skills deactivate
```

When Codex and Claude runtime directories both exist, this default form removes managed links from both runtimes automatically.

Examples with explicit runtime selection:

```bash
mpt-skills deactivate --codex
mpt-skills deactivate --claude
mpt-skills deactivate --all
```

`deactivate` removes only the managed skill links from the selected runtime directories.
It does not delete installed versions from `~/.mpt-extension-skills` and does not remove the version metadata stored in the package install root.

## Remove Everything

Use:

```bash
mpt-skills remove --all
```

This command:

- removes managed skill links from detected Codex and Claude runtime directories
- removes the user command link from `~/.local/bin` or `MPT_SKILLS_BIN_DIR`
- removes the package install root such as `~/.mpt-extension-skills`

This is the destructive cleanup command.
Use it when you want to remove the installed package entirely, not just detach runtime links.

## Manual Copy Is Not Recommended

Do not install individual skills by manually copying only `skills/<skill-name>` into a runtime directory unless you are debugging locally.

Manual copying is discouraged because:

- it does not install shared `standards/`, `knowledge/`, and `docs/`
- installed version metadata is lost
- updates and rollback become manual
- local documentation links may break

## Related Documents

- [testing.md](./testing.md)
- [../scripts/mpt-skills.sh](../scripts/mpt-skills.sh)
