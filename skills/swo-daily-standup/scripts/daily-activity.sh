#!/usr/bin/env bash
# daily-activity.sh
# Prints a standup-ready summary of JIRA tickets and GitHub activity from yesterday and today.
# Filtered: GitHub output includes only softwareone-platform org.

set -euo pipefail

YESTERDAY=$(date -v-1d +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)
GH_ORG="softwareone-platform"

echo "═══════════════════════════════════════════"
echo "  Daily Activity Summary — ${YESTERDAY} → ${TODAY}"
echo "═══════════════════════════════════════════"

# ─── JIRA ───────────────────────────────────────
echo ""
echo "📋 JIRA — Updated Yesterday & Today"
echo "───────────────────────────────────────────"

JQL="(reporter = currentUser() OR assignee = currentUser()) AND updated >= \"${YESTERDAY}\" AND updated <= \"${TODAY}\""

acli jira workitem search \
  --jql "${JQL}" \
  --fields "key,issuetype,status,summary" \
  2>/dev/null || echo "  (no results or acli error)"

# ─── GITHUB PRs ─────────────────────────────────
echo ""
echo "🔀 GitHub PRs — softwareone-platform"
echo "───────────────────────────────────────────"

gh search prs \
  --author albertsola \
  --owner "${GH_ORG}" \
  --updated "${YESTERDAY}..${TODAY}" \
  --json number,title,state,url,repository \
  --limit 50 \
  2>/dev/null \
| python3 -c "
import sys, json
prs = json.load(sys.stdin)
if not prs:
    print('  (none)')
else:
    for pr in prs:
        repo = pr['repository']['nameWithOwner']
        print(f\"  [{pr['state']}] #{pr['number']} {pr['title']}\")
        print(f\"          {repo}  {pr['url']}\")
" 2>/dev/null || echo "  (no results or gh error)"

# ─── GITHUB COMMITS ─────────────────────────────
echo ""
echo "📝 GitHub Commits — softwareone-platform"
echo "───────────────────────────────────────────"

gh api "/users/albertsola/events?per_page=100" \
  2>/dev/null \
| python3 -c "
import sys, json
events = json.load(sys.stdin)
since = '${YESTERDAY}'
until = '${TODAY}'
seen = set()
for e in events:
    if e['type'] != 'PushEvent':
        continue
    if not e['repo']['name'].startswith('${GH_ORG}/'):
        continue
    event_date = e['created_at'][:10]
    if not (since <= event_date <= until):
        continue
    repo = e['repo']['name']
    for commit in e.get('payload', {}).get('commits', []):
        sha = commit['sha'][:7]
        msg = commit['message'].splitlines()[0]
        key = (repo, sha)
        if key not in seen:
            seen.add(key)
            print(f'  {repo}  [{sha}]  {msg}')
if not seen:
    print('  (none)')
" 2>/dev/null || echo "  (no results or gh error)"


# ─── OPEN JIRA TICKETS ──────────────────────────
echo ""
echo "🗂  JIRA — Open Tickets"
echo "───────────────────────────────────────────"

acli jira workitem search \
  --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC" \
  --fields "key,issuetype,status,summary" \
  2>/dev/null || echo "  (no results or acli error)"

echo ""
echo "═══════════════════════════════════════════"
