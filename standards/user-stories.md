# User Story & Work Breakdown Standard

## Owner
Sirius Team

## Scope

Applies to:
- breaking an epic or a Technical Design Review (TDR) into user stories and subtasks in Jira
- estimating, componentizing, and sprinting that work

## Purpose

Define how to turn an epic or TDR into a clean, demoable, estimable backlog of user stories and subtasks, so the breakdown is consistent across people and repositories.

## Definitions

- A `user story` is a self-contained, demoable slice of value, written as `As a <persona>, I want <capability>, so that <benefit>`.
- An `enabler story` is a technical/platform story with no human end-user persona; its persona is an internal role (for example, `extension developer`, `contrib maintainer`).
- A `subtask` is one implementation unit under a story. In this Jira there are two subtask types: `Back` (backend) and `Front` (frontend).
- The `TDR` (Technical Design Review) is the design/investigation artifact for an epic.

## Splitting Principles

1. Apply INVEST: each story is Independent, Negotiable, Valuable, Estimable, Small, Testable.
2. Slice vertically. A story delivers an end-to-end, demoable result, not a horizontal technical layer.
3. Every story must be self-contained, and finishing it must produce a result that can be shown at a demo.
4. A story's implementation must fit within one sprint (**2 weeks**). If it does not, split it further.
5. A story may span several components. Do not force one component per story.
6. Prefer enabler stories for platform/infrastructure work; use an internal-role persona instead of inventing an end user.

## Two-Phase Breakdown

1. Phase 1 — split the epic/TDR into all user stories first. Agree the story list before creating subtasks.
2. Phase 2 — revisit each story and create its subtasks.

Do not interleave the two phases. Do not embed subtasks as text inside the story description; create them as real Jira subtask issues in Phase 2.

## Stories

- Inherit from the parent epic: `Team`, `components`, `fixVersions` — unless explicitly overridden.
- Do **not** set the `Keywords` field on a user story, even when the epic has one.
- Set the `Sprint` on the **story** only; subtasks inherit the sprint from their parent story.
- The `Design, investigate and research` story is a special initial story — see the initial-epic task skill. It is the only story type that carries an Original Estimate directly (3d).

## Subtasks

- Use `Back` and `Front` types. A single story may mix both; backend and frontend work in one story is normal and is not a reason to split.
- Do **not** create a standalone subtask for writing tests. Code is always committed together with its tests, so testing is part of each implementation subtask.
- Do **not** add a `Design, investigate and research` subtask by default. The TDR already is the design/investigation artifact. Add design work only when the user explicitly asks for design beyond the TDR.
- Subtasks inherit `Team` and `Sprint` from the parent story. Do not set `Team` on a subtask (Jira rejects it).
- **Never assign a `Sprint` directly to a subtask.** Sprint is set on the user story only; subtasks follow their parent automatically.

## Estimates

- Put the Original Estimate on **subtasks** (the implementation work).
- A normal story carries no Original Estimate; it rolls up from its subtasks.
- Exception: the initial `Design, investigate and research` story carries a `3d` Original Estimate directly (it has no subtasks).
- Sizing: the team sprint is 2 weeks (10 working days). Use day-scale estimates (for example `0.5d`, `1d`, `2.5d`). Determine estimates yourself from the work; the user can adjust.

## Components

- Determine the `components` yourself from what the work actually touches. Do not ask.
- A story or subtask may have **several** components.
- Heuristic:
  - core/shared-library work → the shared-library/SDK component (for example `Extension SDK`)
  - work that modifies a specific extension → that extension's component (for example `Extension Adobe`, `Extension AWS`) plus the shared component
  - a per-repository subtask gets that repository's component
- Set the **epic's** components to the union of every component its child stories touch.

## Backport

- If the epic carries a `backport` fix version, always propose a **separate** backport user story. Never fold backport work into the main story.

## Dependencies

- Link dependent stories explicitly. When story B can only start after story A is delivered, mark A `blocks` B.

## Related Documents

- [skills.md](./skills.md)
