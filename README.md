# mpt-extension-skills

Custom AI agent skills for MPT extensions.

## Skills in this repository

- `swo-gh-commit-pr`: Git commit + GitHub PR workflow skill.

## Prerequisites

- A local agent/tool runtime that supports file-based skills
- Access to your skills home directory (`~/.codex`, `~/.claude`, etc.)

## Install from a local clone

From this repository root:

```bash
# Codex example
cp -R swo-gh-commit-pr ~/.codex/skills/
```

### Claude Code examples

Project-local install (recommended):

```bash
mkdir -p .claude/skills
cp -R swo-gh-commit-pr .claude/skills/
```

If you use a custom Claude config directory:

```bash
mkdir -p "${CLAUDE_CONFIG_DIR}/skills"
cp -R swo-gh-commit-pr "${CLAUDE_CONFIG_DIR}/skills/swo-gh-commit-pr"
```

## Install directly from GitHub

If your runtime provides a skill-installer helper script:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo softwareone-platform/mpt-extension-skills \
  --path swo-gh-commit-pr \
  --name swo-gh-commit-pr
```
