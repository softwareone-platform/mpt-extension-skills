# Teams notification destination configuration

How the task resolves *which* Teams chat a PR-ready notification goes to, and
where the secret webhook URL comes from. The goal: a different destination per
project or team, with the webhook URL (a secret) never stored in git.

## Secret storage

The webhook URL always lives in an **environment variable**. It is never written
to a repository file, printed, or passed on a command line. The resolver script
only ever reports the *name* of the variable to read, never its value.

## Env-var naming convention

A logical destination name maps to an environment variable by convention:

```text
<destination>  ->  MPT_TEAMS_WEBHOOK_<DESTINATION>
```

where `<DESTINATION>` is the destination upper-cased with every run of
non-alphanumeric characters replaced by `_`. Examples:

```text
team-backend   ->  MPT_TEAMS_WEBHOOK_TEAM_BACKEND
team-frontend  ->  MPT_TEAMS_WEBHOOK_TEAM_FRONTEND
```

The single default variable `MPT_TEAMS_WEBHOOK_URL` is used when no destination
is selected.

## Resolution precedence

1. `--to <destination>` — explicit per-run override (`/mpt-notify-pr-ready --to team-backend`).
2. `MPT_TEAMS_WEBHOOK_URL` — the default variable, when it is set and non-empty.
3. `.mpt/notifications.yaml` `default_destination` — the project default.

The `resolve_teams_destination.py` script implements this precedence and reports
`resolved: false` (with a reason) when the chosen variable is not set, so the
task can stop with a clear blocker instead of posting nowhere.

## Optional per-project file: `.mpt/notifications.yaml`

Only needed when a repository wants a project default destination or a
non-conventional env-var name. It holds names, never the URL:

```yaml
teams:
  default_destination: team-backend
  destinations:
    team-backend:  { webhook_env: MPT_TEAMS_WEBHOOK_TEAM_BACKEND }
    team-frontend: { webhook_env: MPT_TEAMS_WEBHOOK_TEAM_FRONTEND }
```

The task reads this small file when present and passes its values to the
resolver:

- `default_destination` → `--default-destination`
- a destination's explicit `webhook_env` (only when it does not follow the
  convention) → `--webhook-env`

When the file is absent, the convention plus `MPT_TEAMS_WEBHOOK_URL` is enough.
