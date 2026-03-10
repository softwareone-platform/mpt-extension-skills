# mpt-extension-skills

Custom AI agent skills for MPT extensions.

## Skills in this repository

- `swo-gh-commit-pr`: Git commit + GitHub PR workflow skill.

## Prerequisites

- A local agent/tool runtime that supports file-based skills
- Access to your skills home directory (`~/.codex`, `~/.claude`, etc.)

## Install directly from GitHub

If your runtime includes a GitHub skill-installer capability, use this prompt in your agent chat:

```text
install swo-gh-commit-pr from https://github.com/softwareone-platform/mpt-extension-skills
```


## Install from a local clone

From this repository root:

```bash
# Codex example
cp -R swo-gh-commit-pr ~/.codex/skills/
```

### Claude Code examples

Project-local install:

```bash
mkdir -p .claude/skills
cp -R swo-gh-commit-pr .claude/skills/
```

If you use a custom Claude config directory:

```bash
mkdir -p "${CLAUDE_CONFIG_DIR}/skills"
cp -R swo-gh-commit-pr "${CLAUDE_CONFIG_DIR}/skills/swo-gh-commit-pr"
```
