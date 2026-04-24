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

## Related Documents

- [usage.md](./usage.md)
- [testing.md](./testing.md)
- [../scripts/mpt-extensions-skills-install.sh](../scripts/mpt-extensions-skills-install.sh)
