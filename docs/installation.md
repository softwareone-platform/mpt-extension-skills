# Installation

## Purpose

Describe the first-time installation paths for the shared skills package: the CLI
shell installer from GitHub Releases, the versioned plugin for runtimes with a
marketplace, and the Cursor rule adapter.

## Prerequisites

- Bash
- `curl`
- `tar`
- Access to a local user bin directory such as `~/.local/bin`
- A local agent/tool runtime that supports file-based skills, such as Codex or Claude

The shell installer and the plugin are delivery paths for the same skills; use
whichever the runtime supports.

## Install via CLI

Install the latest GitHub release with the release installer asset:

```bash
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash
```

Install a specific release version:

```bash
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/download/1.0.0/mpt-extensions-skills-install.sh | bash
```

### Runtime selection

By default, the installer auto-detects installed runtimes and wires only those.
Pass runtime flags through the shell command when explicit targeting is needed:

```bash
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash -s -- --all
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash -s -- --codex
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash -s -- --claude
```

### Installed command

The installer exposes the CLI as:

```bash
mpt-extensions-skills
```

By default this command is linked into:

```text
~/.local/bin/mpt-extensions-skills
```

For lifecycle commands after installation, see [usage.md](./usage.md).

## Install as a plugin

Runtimes that support a plugin marketplace can install the skills as a versioned
plugin instead of using the shell installer. Each release pins the plugin source
to its git tag for reproducible installs.

### Claude Code plugin

```text
/plugin marketplace add softwareone-platform/mpt-extension-skills
/plugin install mpt-extension-skills@mpt-extension-skills
```

### Codex plugin

```bash
codex plugin marketplace add softwareone-platform/mpt-extension-skills
```

Then open `/plugins`, select the marketplace, and install `mpt-extension-skills`.

Codex reads `.agents/plugins/marketplace.json`, whose plugin `source` is pinned
to the release tag, so the install is reproducible rather than tracking `main`.

### Cursor rule adapter

Cursor has no versioned plugin marketplace, so the rule adapter is installed
per project rather than into a global runtime directory.

Let the CLI install the adapter for you (recommended) — `--cursor` copies the
versioned adapter into a project's `.cursor/rules/`:

```bash
# Into the current directory's .cursor/rules/
mpt-extensions-skills install --version <version> --cursor

# Into a specific project directory's .cursor/rules/
mpt-extensions-skills install --version <version> --cursor=/path/to/repo
```

`--cursor` is explicit-only: it is never auto-detected and is not included by
`--all`, and it can be combined with `--codex`/`--claude`. Remove a project's
adapter with `mpt-extensions-skills deactivate --cursor=/path/to/repo`. The
target directory can also be set with the `CURSOR_PROJECT_DIR` environment
variable.

Alternatively, copy the rule adapter at
[../.cursor/rules/mpt-extension-skills.mdc](../.cursor/rules/mpt-extension-skills.mdc)
into the consuming repository's `.cursor/rules/` directory by hand.

The adapter and the skills do not link `standards/` and `knowledge/` with
repo-relative paths, so installing the `.mdc` alone never strands those
references. Shared docs are resolved at use time from the CLI-installed root
`${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when present,
and otherwise from the `main` branch of the shared GitHub repository. For a
Cursor-only setup that means the standards resolve through the GitHub `main`
fallback unless you also run the [CLI installer](#install-via-cli) above (which
the `--cursor` flag does), populating the local root regardless of which
runtimes are wired.

## Commands and Hooks

The plugin path also installs the slash commands in `commands/` and the
`SessionStart` hook in `hooks/`, both auto-discovered from the plugin root. Hooks
are executable and require a one-time trust step (in Codex, via `/hooks`).

The shell installer wires the slash commands into the Claude commands directory
(default `~/.claude/commands`, override with `CLAUDE_COMMANDS_DIR`) alongside the
skills, and `deactivate` removes them. The shell installer does not register
hooks; install the plugin to get the `SessionStart` hook.

## Related Documents

- [usage.md](./usage.md)
- [testing.md](./testing.md)
- [../scripts/mpt-extensions-skills-install.sh](../scripts/mpt-extensions-skills-install.sh)
