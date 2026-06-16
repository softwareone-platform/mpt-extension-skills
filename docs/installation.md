# Installation

## Purpose

Describe the first-time installation path for the shared skills package from GitHub Releases.

## Prerequisites

- Bash
- `curl`
- `tar`
- Access to a local user bin directory such as `~/.local/bin`
- A local agent/tool runtime that supports file-based skills, such as Codex or Claude

## Install Latest Release

Install the latest GitHub release with the release installer asset:

```bash
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash
```

## Install Specific Release

Install a specific release version:

```bash
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/download/1.0.0/mpt-extensions-skills-install.sh | bash
```

## Runtime Selection

By default, the installer auto-detects installed runtimes and wires only those.
Pass runtime flags through the shell command when explicit targeting is needed:

```bash
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash -s -- --all
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash -s -- --codex
curl -LsSf https://github.com/softwareone-platform/mpt-extension-skills/releases/latest/download/mpt-extensions-skills-install.sh | bash -s -- --claude
```

## Installed Command

The installer exposes the CLI as:

```bash
mpt-extensions-skills
```

By default this command is linked into:

```text
~/.local/bin/mpt-extensions-skills
```

For lifecycle commands after installation, see [usage.md](./usage.md).

## Plugin Installation

Runtimes that support a plugin marketplace can install the skills as a versioned
plugin instead of using the shell installer. Each release pins the plugin source
to its git tag for reproducible installs.

Claude Code:

```text
/plugin marketplace add softwareone-platform/mpt-extension-skills
/plugin install mpt-extension-skills@mpt-extension-skills
```

Codex:

```bash
codex plugin marketplace add softwareone-platform/mpt-extension-skills
```

Then open `/plugins`, select the marketplace, and install `mpt-extension-skills`.

Codex reads `.agents/plugins/marketplace.json`, whose plugin `source` is pinned
to the release tag, so the install is reproducible rather than tracking `main`.

Cursor has no versioned plugin marketplace. Copy the rule adapter at
[../.cursor/rules/mpt-extension-skills.mdc](../.cursor/rules/mpt-extension-skills.mdc)
into the consuming repository's `.cursor/rules/` directory.

The shell installer and the plugin are two delivery paths for the same skills;
use whichever the runtime supports.

## Related Documents

- [usage.md](./usage.md)
- [testing.md](./testing.md)
- [../scripts/mpt-extensions-skills-install.sh](../scripts/mpt-extensions-skills-install.sh)
