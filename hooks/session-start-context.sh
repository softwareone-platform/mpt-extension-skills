#!/usr/bin/env bash
#
# SessionStart hook: inject a compact MPT extension SDLC reminder and the list of
# available slash commands. Output goes to stdout, which Claude Code adds to the
# session context. Always exits 0 so it can never block a session.
#
set -euo pipefail

cat <<'EOF' || true
MPT extension SDLC is available in this session.

Shared standards live under the plugin's standards/ (commit-messages, pull-requests,
python-coding, testing, documentation, dependencies). Follow them; do not restate or
contradict them. Operational how-tos are in knowledge/. For any concrete SDLC step,
prefer the matching mpt-ext-* skill instead of hand-rolling.

SDLC slash commands (thin wrappers over the workflow skills):
- /mpt-start-work <KEY> <type>   start a Jira issue: branch + In Progress
- /mpt-send-to-review            docs + validate + PR + Jira Code Review
- /mpt-address-review           handle PR review feedback
- /mpt-complete-after-merge     post-merge Jira handoff
- /mpt-decompose-tdr <KEY>      break an epic/TDR into stories + subtasks
- /mpt-fix-dependabot           process Dependabot PRs
- /mpt-hotfix-backport <KEY>    hotfix/backport to the active release branch
- /mpt-skill-authoring [purpose] create or update a reusable shared skill
EOF

exit 0
