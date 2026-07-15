---
name: mpt-ext-task-start-jira-work
description: Only move Jira state when starting work: transition the issue and its parent chain to In Progress, ensure active-sprint placement, and check reassignment. Does not create a branch.
---

# Start Jira Work

## Purpose

Prepare a Jira issue for active development by setting the correct working state.

## Use When

- The user starts work on a Jira issue.
- The issue should move to `In Progress`.
- Parent issues should also move to `In Progress`.
- The issue must be checked against the active sprint.
- The assignee must be checked against the current Jira-authenticated user.

## Do Not Use When

- The task is only to create or switch Git branches.
- The task is only to open or update a pull request.
- The task is only to read Jira issue data without changing working state.
- The task is to finish development and move the issue to `Code Review` or `QA`.

## Inputs

- Jira issue key.
- Optional sprint or board context when the active sprint cannot be determined automatically.
- Optional user confirmation when reassignment or sprint changes are needed.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Jira authentication is active and the current user can read, transition, and update the target issue and its parent chain.
- The current user has the Jira permissions needed for state transitions, sprint updates, and assignee changes when confirmed by the user.
- The repository or board context is sufficient to determine the active sprint, or the user is available to provide the missing board or sprint context before changes are made.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Read the Jira issue and Jira auth context.
- Use `mpt-ext-tool-jira-workitem-ops` to fetch the current issue state.
- Determine the currently authenticated Jira user from Jira auth context.

3. Resolve the full parent chain.
- Read the direct parent of the issue if it exists.
- Continue reading parent issues until the full parent chain is known.
- Stop only when the chain has no further parent.
- Stop and report a Jira hierarchy blocker if more than 10 parent links are traversed.

4. Move the issue and parent chain to `In Progress`.
- Transition the current issue to `In Progress` when it is not already there.
- Transition each parent issue in the chain to `In Progress` when it is not already there.
- Preserve already-correct status values rather than rewriting them unnecessarily.

5. Resolve active sprint and sprint target.
- Check whether the Jira issue already belongs to an active sprint in the Sprint field (resolve its ID from `standards/jira-fields.md`).
- If it already has an active sprint, preserve sprint placement and report it as already correct.
- If the issue has only closed or future sprint entries, derive the board id from the Sprint field's `boardId` entries.
- If the target issue is a subtask and does not expose useful sprint history, read the direct parent and derive the board id from the parent sprint history.
- If no board id can be determined from the issue or the relevant parent, ask the user for the correct board id before changing sprint placement.
- Resolve the active sprint for the board with:

```bash
acli jira board list-sprints --id <board-id> --state active --json
```

- If the board has no active sprint, stop and report the sprint blocker.
- If multiple active sprints are returned, stop and ask the user which sprint should be used.

6. Apply sprint placement to the correct issue.
- Read `issuetype.subtask` for the target issue before editing sprint placement.
- If `issuetype.subtask` is `false`, add the active sprint to the target issue itself.
- If `issuetype.subtask` is `true`, do not add sprint to the subtask directly. Jira subtasks inherit sprint placement from their direct parent, and Jira rejects direct subtask sprint assignment.
- For subtasks, add the active sprint to the direct parent issue instead, then re-read the original subtask and verify that it shows the active sprint through inheritance.
- If the direct parent already has the active sprint, preserve it and only verify the subtask.
- If editing arbitrary Jira fields is not supported by the available CLI command, use the available Jira issue edit API or connector for the sprint field. If no safe edit path exists, stop and report the blocker instead of guessing a payload.

7. Verify assignee.
- Compare the issue assignee with the current Jira-authenticated user.
- If they differ, ask the user whether the issue should be reassigned to the current Jira user.
- Reassign only when the user confirms.

8. Report the result clearly.
- State whether the issue moved to `In Progress`.
- State whether any parent issues moved to `In Progress`.
- State whether sprint placement changed.
- State which issue received the sprint update: the target issue itself, or the direct parent when the target is a subtask.
- State the active sprint name and id when resolved.
- State whether reassignment was requested, skipped, or completed.

## Guardrails

- Never assume the active sprint if Jira context is ambiguous.
- Never use JQL `openSprints()` as the only active-sprint resolution path when a board id is available; prefer `acli jira board list-sprints --id <board-id> --state active --json`.
- Never assign sprint directly to a subtask. Update the direct parent and verify inherited sprint placement on the subtask.
- Never silently move a parent to a sprint when the target is a subtask without reporting that the parent was the sprint edit target.
- Never reassign the issue automatically when the assignee differs from the current Jira-authenticated user.
- Never stop at the direct parent when a longer parent chain exists.
- Never traverse more than 10 parent links without stopping and reporting a Jira hierarchy blocker.
- Never rewrite already-correct Jira state without need.
- Never mix branch creation or PR operations into this task.

## Expected Outcome

The Jira issue and its full parent chain are in `In Progress`, the issue is placed in the active sprint when required, assignee mismatches are surfaced for confirmation, and any blockers are reported clearly.
