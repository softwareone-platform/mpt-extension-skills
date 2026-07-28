---
name: mpt-ext-workflow-notify-pr-ready
description: Run the on-demand flow that notifies a Microsoft Teams chat when a reviewed PR is green — all checks pass and CodeRabbit approved. Evaluates once and stops; it does not wait for review.
---

# Notify PR Ready

## Purpose

Coordinate the on-demand step that publishes a pull request's details to a Microsoft Teams chat once the PR is green: all required checks pass and CodeRabbit has approved.

## Use When

- A developer wants to announce, on demand, that a reviewed PR is ready.
- CodeRabbit has already run and the PR is expected to be green.
- The team is notified in a Teams chat that may vary per project.

## Do Not Use When

- CodeRabbit has not run yet and the flow would need to wait or poll for it.
- The task is only to post an arbitrary Teams message.
- The task is to open or update the PR, transition Jira, or handle review comments.

## Inputs

- The target PR: a PR number or the current branch's PR.
- Optional `--to <destination>` override for the Teams destination.
- GitHub authentication to read PR checks and reviews.
- The Teams webhook URL available through an environment variable (never committed).
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- The notification is triggered on demand, after CodeRabbit has finished; this flow evaluates the gate once and stops rather than waiting.
- The repository's CodeRabbit configuration submits a formal `APPROVED` review when clean, so the gate can pass.
- Destination resolution and delivery are handled by the underlying task and tool skills.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Notify when the PR is green.
- Use `mpt-ext-task-notify-pr-ready-in-teams` for the target PR, passing the optional `--to` destination through.
- Let that task read the PR, evaluate the green gate once, resolve the destination, render the card, and deliver it through the Teams tool.
- Act on its returned outcome: report delivery on success; on a failed gate or unresolved destination, stop and report the exact blocker it returns. Do not wait or poll.

3. Report the handoff clearly.
- State whether the notification was sent and to which destination environment variable (name only).
- When nothing was sent, state whether the PR was not green (with the reasons) or the destination was unresolved.

## Guardrails

- Never wait, poll, or retry for CodeRabbit; delegate a single check-once evaluation to the task.
- Never post when the green gate fails or the destination is unresolved.
- Never reimplement the green evaluation, destination resolution, or message delivery owned by the underlying task and tool skills.
- Never mix PR creation, Jira transitions, or review-comment handling into this workflow.
- Prefer the narrower task skill when the user only wants the notification step without workflow reporting.

## Shared References

- `mpt-ext-task-notify-pr-ready-in-teams` — evaluate the green gate, resolve the destination, and deliver the notification.

## Expected Outcome

When the PR is green, its details are delivered to the correct Teams chat on demand; otherwise nothing is sent and the developer receives a clear reason.
