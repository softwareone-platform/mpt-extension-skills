---
name: swo-daily-standup
description: Generate a standup summary (Done, Doing, Todo, Blockers) when the user asks for a daily standup, yesterday's activity, or what they worked on. Gathers data from JIRA (via acli) and GitHub (via gh), scoped to the softwareone-platform org, and synthesises a paste-ready message.
---

# Daily Standup

Gather yesterday's and today's activity from JIRA and GitHub and present it as a standup message.

## Trigger

Use this skill when the user asks for:
- daily standup / standup summary
- what did I do yesterday / today
- activity summary
- done / doing / todo report

## Workflow

1. **Gather data** by running the bundled script or issuing the commands below directly.
   - The script handles macOS date arithmetic, org scoping, and deduplication.
   - If the script is not available, run the command patterns in the next section manually.

2. **Classify tickets** using the following rules:

   | Category | Criteria |
   |----------|----------|
   | ✅ Done | JIRA status = Done **and** updated in window; or GitHub PR state = merged |
   | 🔄 Doing | JIRA status = In Progress **and** updated in yesterday/today window |
   | 📋 Todo | Open tickets (In Progress, New, Code Review, Backlog) **not** updated in window; open PRs |
   | 🚧 Blockers | Never inferred from data alone — always ask the user |

3. **Output** a paste-ready standup in this format:

```
✅ Done
- [KEY] Summary (PR #N if applicable)

🔄 Doing
- [KEY] Summary

📋 Todo
- [KEY] Summary

🚧 Blockers
- None / <user-provided>
```

4. **Surface anomalies** inline (do not block output):
   - Duplicate tickets with identical summaries
   - In Progress tickets with no recent update (stale)
   - PRs open for more than 2 days

## Command Patterns

```bash
# Compute date range (macOS)
YESTERDAY=$(date -v-1d +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)
GH_ORG="softwareone-platform"

# JIRA: tickets updated yesterday and today (assigned or reported by current user)
acli jira workitem search \
  --jql "(reporter = currentUser() OR assignee = currentUser()) AND updated >= \"${YESTERDAY}\" AND updated <= \"${TODAY}\"" \
  --fields "key,issuetype,status,summary" \
  --json

# JIRA: all open tickets assigned to current user
acli jira workitem search \
  --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC" \
  --fields "key,issuetype,status,summary" \
  --json

# GitHub PRs updated in window, scoped to softwareone-platform
gh search prs \
  --author albertsola \
  --owner "${GH_ORG}" \
  --updated "${YESTERDAY}..${TODAY}" \
  --json number,title,state,url,repository \
  --limit 50

# GitHub commits via Events API (covers last ~300 events)
gh api "/users/albertsola/events?per_page=100" \
  | python3 -c "
import sys, json
events = json.load(sys.stdin)
for e in events:
    if e['type'] != 'PushEvent': continue
    if not e['repo']['name'].startswith('softwareone-platform/'): continue
    date = e['created_at'][:10]
    for c in e.get('payload', {}).get('commits', []):
        print(date, e['repo']['name'], c['sha'][:7], c['message'].splitlines()[0])
"
```

## Bundled Script

`scripts/daily-activity.sh` — runs all queries and prints structured terminal output.

```bash
bash scripts/daily-activity.sh
```

Output sections:
- `📋 JIRA — Updated Yesterday & Today`
- `🔀 GitHub PRs — softwareone-platform`
- `📝 GitHub Commits — softwareone-platform`
- `🗂  JIRA — Open Tickets`

Parse the sections, then apply the classification table above to generate the standup message.

## Guardrails

- Never assume blockers from JIRA data — only report if user states them.
- GitHub scope is strictly `softwareone-platform` org; personal repos and `Tardix`/`EffortlessWebsite` orgs are excluded.
- If `acli` or `gh` returns an auth error, report it and stop — do not produce a partial standup silently.
- If the window spans a weekend, note that no activity on Saturday/Sunday is expected.
- Do not duplicate tickets that appear in both the "updated" query and the "open tickets" query.
