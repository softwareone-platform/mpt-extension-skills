# Skill Authoring Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - reusable skills stored in shared skill repositories

## Purpose
Define shared expectations for writing reusable skills that are clear, scoped, maintainable, and safe to apply across repositories and workflows.

## Definitions

- A `skill` is a reusable instruction package centered around a `SKILL.md` entry point.
- A `tool skill` explains how to use a specific tool, integration, or interface.
- A `task skill` describes how to complete one repeatable task with a clear outcome.
- A `workflow skill` coordinates multiple steps or tasks into an end-to-end process.
- `Shared guidance` is information that already belongs in `standards/` or `knowledge/` and should be linked instead of copied.

## General Rules

1. Every skill must have a single clear responsibility.
2. Every skill must fit exactly one type:
 - `tool`
 - `task`
 - `workflow`
3. Every shared skill folder name must start with the `mpt-ext-` prefix.
4. The skill type must be part of the skill name.
5. Shared skills must use this naming pattern:

```text
mpt-ext-<type>-<short-purpose>
```

Examples:

- `mpt-ext-tool-jira-workitem-ops`
- `mpt-ext-task-send-pr`
- `mpt-ext-workflow-start-work`

6. Keep the `<short-purpose>` segment concise, explicit, and action-oriented.
7. Do not mix multiple responsibility levels in one skill. A skill must not act as a tool reference, an atomic task, and a full workflow at the same time.
8. Every skill must include a `SKILL.md` file as its entry point.
9. Every shared skill must include `agents/openai.yaml`.
10. Skill instructions must be reusable. Do not write a skill for a one-off case that will not repeat.
11. A `tool` skill must focus on one tool or integration and explain how to use it correctly.
12. A `task` skill must describe one bounded task with a clear expected result.
13. A `workflow` skill must coordinate a broader process made of multiple steps or task-level actions.
14. A `tool` skill must not orchestrate other skills.
15. A `task` skill may rely on tools, but it should not turn into a broad workflow.
16. A `workflow` skill may reference or rely on task-level actions, but it should not hide unrelated side effects or branch into multiple unrelated processes.
17. Avoid deep or ambiguous composition between skills. Keep the execution model easy to understand from reading the skill.
18. Do not duplicate shared standards or shared operational guidance inside a skill. Link to the relevant document in `standards/` or `knowledge/` instead.
19. When a skill links to shared `standards/`, `knowledge/`, or package documentation, it must use local installed paths only. Do not rely on GitHub URLs or other remote links for required execution context.
20. When resolving shared package documents at runtime, look in the installed package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

Use paths under that root such as `standards/skills.md`, `standards/documentation.md`, `knowledge/...`, or `docs/...` when the skill needs shared guidance from this package.
21. Do not treat repository-specific behavior as reusable truth unless the skill is explicitly intended for that repository or repository family.
22. Write skills in direct, operational language. Prefer explicit instructions and guardrails over narrative explanation.
23. State destructive or high-risk actions explicitly. Do not hide them inside vague steps.
24. Keep examples short, concrete, and directly relevant to the skill.
25. Add supporting files only when they materially improve reuse, correctness, or maintainability.

## Required Structure

Every skill folder must contain:

```text
<skill-name>/
  SKILL.md
  agents/
    openai.yaml
```

Optional supporting structure:

```text
<skill-name>/
  SKILL.md
  agents/
    openai.yaml
  references/
  scripts/
  assets/
```

Use optional directories only when they serve a clear purpose:

- `references/`: supporting material that is too detailed to inline in `SKILL.md`
- `scripts/`: reusable automation that reduces error-prone manual execution
- `assets/`: non-code supporting assets required by the skill

Do not add placeholder folders or speculative files for future use.

## Required OpenAI Adapter

Every shared skill must include `agents/openai.yaml`.

This file is required so the same shared skill can be used in Codex/OpenAI-style environments while remaining compatible with Claude-style `SKILL.md` consumption.

Minimum required shape:

```yaml
interface:
  display_name: "<Human readable name>"
  short_description: "<Short summary>"
  default_prompt: "<Default prompt>"
```

Required field expectations:

- `display_name`: short human-readable name for the skill
- `short_description`: concise summary of the skill purpose
- `default_prompt`: default runtime prompt aligned with the skill scope and intent

`SKILL.md` remains the main behavior document, but `agents/openai.yaml` is a required adapter for cross-runtime compatibility.

## SKILL.md Requirements

Every `SKILL.md` must include these required fields or sections:

1. `Title`
- A short human-readable skill name.

2. `Purpose`
- A concise statement of what the skill does.

3. `Use When`
- The situations where the skill should be applied.

4. `Do Not Use When`
- The situations where the skill is the wrong choice.

5. `Inputs` or `Prerequisites`
- The required context, access, state, or user input needed before execution.

6. `Workflow`
- The ordered steps the agent should follow.

7. `Guardrails`
- The constraints, checks, and safety rules that must be respected.

8. `Expected Outcome`
- The result the skill is expected to produce.

These may be expressed with equivalent headings, but all of the information above must be present in every skill.

## Recommended SKILL.md Shape

A good `SKILL.md` will usually include sections like:

- a short title
- a concise purpose statement
- input or prerequisite expectations
- a step-by-step workflow
- guardrails and constraints
- expected outputs or result
- examples when helpful

The exact headings may vary, but the content should remain explicit and easy to scan.

## Authoring Guidance

- Prefer narrow skills over broad multi-purpose instructions.
- Keep the skill self-contained, but not bloated.
- Move stable shared policy into `standards/`.
- Move reusable operational how-to material into `knowledge/`.
- Use the skill only for the reusable operational behavior that should be applied by an agent.
- Link to shared documents instead of copying long policy sections into the skill body.
- Use local package paths when linking shared `standards/`, `knowledge/`, or package documentation from a skill.
- Resolve shared package links from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` unless the task is explicitly working in the source repository.
- Keep the top-level flow readable without forcing the reader to open many extra files.
- Use `references/` only for detail that genuinely supports execution.
- Use `scripts/` when the scripted path is safer or more repeatable than prose instructions alone.
- Prefer deterministic steps over open-ended suggestions when the task has a known correct workflow.
- Call out assumptions explicitly when the workflow depends on environment, auth, repository state, or external systems.

## Anti-Patterns

Avoid these patterns:

- a skill that tries to cover multiple unrelated jobs
- a skill that mixes tool reference, task execution, and orchestration in one file
- a skill that mostly duplicates existing standards or knowledge documents
- a skill that contains repository-specific details without saying so
- a skill that hides risky actions behind vague instructions like `fix`, `handle`, or `clean up`
- a skill with long background narrative but no clear execution steps
- a skill that depends on many supporting files without a clear reason
- a skill created for a one-time request instead of a repeatable workflow

## Examples

Good `tool` skill:

- explains how to use one external system or CLI safely
- lists required auth or setup
- highlights common failure modes
- does not try to implement a full business workflow

Good `task` skill:

- describes one repeatable task such as updating a dependency, triaging feedback, or preparing a release artifact
- defines the needed inputs
- gives a bounded sequence of steps
- ends with a clear expected result

Good `workflow` skill:

- coordinates a broader process such as starting work, publishing a release, or handling a multi-step operational flow
- keeps the sequence explicit
- makes cross-step dependencies visible
- avoids swallowing unrelated side effects into the same skill

## Related Documents

- [documentation.md](./documentation.md)
- [pull-requests.md](./pull-requests.md)
