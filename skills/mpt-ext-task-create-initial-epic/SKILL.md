---
name: mpt-ext-task-create-initial-epic
description: Create the initial epic for a new effort - the epic plus one "Design, investigate and research" user story estimated at 3d. Use at kickoff, before detailed breakdown.
---

# Create Initial Epic

## Purpose

Create the starting point of a new effort in Jira: one epic plus a single `Design, investigate and research` user story estimated at `3d`.

## Use When

- A new initiative is kicking off and needs its epic created.
- You want the standard initial shape (epic + one design story) before the work is broken down into delivery stories.

## Do Not Use When

- The epic already exists; only stories/subtasks are missing (use `mpt-ext-workflow-decompose-tdr`).
- You need full decomposition of an epic/TDR into delivery stories and subtasks (use `mpt-ext-workflow-decompose-tdr`).
- You only need a single arbitrary Jira issue (use `mpt-ext-tool-jira-workitem-ops` directly).

## Inputs

- Epic summary.
- Either a BDR (Business Design Review) link **or** a description of what needs to be done. One of the two is mandatory.
- Project key and the required project fields (`components`, `fixVersions`); `Team` when applicable; assignee.
- Installed shared package root when shared guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve them from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository. See Shared References.

2. Confirm the epic body.
- The epic description must contain either a BDR link or a clear description of what needs to be done.
- If neither is available, ask the user for one before creating anything.

3. Create the epic.
- Use `mpt-ext-tool-jira-workitem-ops` to create the epic with the required project fields (`components`, `fixVersions`, `Team` when applicable) and the BDR link or description in the body.

4. Create the `Design, investigate and research` user story.
- Parent it to the epic.
- Title it exactly `Design, investigate and research`.
- Set its Original Estimate to `3d` (this is the one story that carries an estimate directly; see `standards/user-stories.md`).
- Inherit `Team`, `components`, `fixVersions` from the epic. Do not set the `Keywords` field on the story.

5. Report the result.
- Show the created epic key and the design story key with its `3d` estimate.

## Guardrails

- The epic must have a BDR link or a description. Do not create an epic with an empty body.
- Create exactly one story here: `Design, investigate and research` at `3d`. Do not create delivery stories or subtasks in this skill.
- Do not set `Keywords` on the story.
- Follow `standards/user-stories.md` for inheritance, estimates, and components.

## Shared References

- `standards/user-stories.md` — work breakdown, estimates, components, the design-story exception
- `standards/skills.md` — skill authoring rules
- Relies on `mpt-ext-tool-jira-workitem-ops` for the Jira operations.

## Expected Outcome

An epic exists with a BDR link or a description, and a single `Design, investigate and research` user story sits under it with a `3d` Original Estimate, ready for later breakdown.
