---
name: mpt-ext-workflow-skill-authoring
description: Create or update a reusable shared skill: classify it as tool, task, or workflow, apply shared naming and structure rules, keep it concise, add required metadata, and avoid duplicating standards.
---

# Skill Authoring

## Purpose

Create or update a reusable shared skill while treating shared standards and knowledge as the source of truth.

## Use When

- The user wants to add a new shared skill to a repository or shared skills package.
- The user wants to update an existing skill's scope, workflow, metadata, or supporting files.
- The user wants to merge draft skill guidance with shared authoring rules.
- The task requires deciding whether information belongs in the skill itself or in shared `standards/` or `knowledge/`.

## Do Not Use When

- The request is only to execute an existing skill, not to author or modify one.
- The request is a one-off instruction that is not intended to be reusable.
- The content is really a shared policy or reusable operational guide that belongs in `standards/` or `knowledge/` instead of a skill.
- The result would mix unrelated responsibilities into one broad skill.

## Inputs

- The target repository or package that will store the skill.
- The user request or examples that describe what the skill should help an agent do.
- Access to the shared package guidance:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

- Any related shared policy or workflow docs that the skill should reference instead of duplicating.

## Shared References

Read these shared documents before making substantial skill changes, using the resolution rule from `standards/skills.md`:

- `standards/skills.md`
- `standards/documentation.md`
- `docs/installation.md`

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs using the resolution rule from Shared References.

2. Understand the intended reuse.
- Identify the repeatable outcome the skill should support.
- Ask for or infer 1-3 concrete example requests that should trigger the skill.
- Stop if the work is clearly a one-off instruction rather than a reusable skill.

3. Decide what belongs in the skill.
- Move cross-repository policy into local `standards/` documents.
- Move reusable how-to or operational guidance into local `knowledge/` documents.
- Keep only the reusable execution behavior that an agent should apply directly inside the skill.

4. Classify the skill before naming it.
- Read `standards/skills.md` using the Shared References resolution rule, and use it as the source of truth for skill type, naming, required sections, structure, and anti-patterns.
- Choose exactly one skill type and keep the responsibility narrow.

5. Resolve shared package links.
- Prefer the installed package root defined by the skill standard:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

- Build links to shared `standards/`, `knowledge/`, and `docs/` from that root for runtime use.
- Use repo-local fallback links only when the task is explicitly happening inside the source repository.
- If the installed root is unavailable and repo-local paths do not apply, use the fallback defined by `standards/skills.md`.

6. Name the skill with the shared convention.
- Apply the naming convention from the installed skill standard instead of restating it locally.
- Make the folder name exactly match the skill name.

7. Plan the minimum useful structure.
- Follow the required and optional structure from the installed skill standard.
- Add only the supporting directories that materially improve correctness, reuse, or maintainability.
- For Python scripts, require Python 3.12 or later as `python3` and include a clear runtime guard for older interpreters.

8. Write `SKILL.md` for fast execution.
- Keep frontmatter limited to `name` and `description`.
- Make the description do the trigger work: say what the skill does and when to use it.
- Write the body in direct operational language.
- Include every required section defined by the installed skill standard.
- Use imperative instructions and short concrete examples.

9. Review the draft for duplicated shared guidance.
- Compare the draft skill against every relevant shared `standards/`, `knowledge/`, and package `docs/` reference.
- Remove copied policy, detailed how-to guidance, or reusable operational rules that already belong to shared docs.
- Replace duplicated material with direct references that use the Shared References resolution rule.
- Keep only skill-specific execution behavior and non-obvious guardrails in `SKILL.md`.

10. Review deterministic operations.
- Identify calculations, parsing, rendering, validation, file generation, JSON/YAML transformations, naming decisions, and repeatable classification logic described in prose.
- Move deterministic operations into `scripts/` when a script is safer or more repeatable than agent interpretation.
- Keep deterministic behavior in prose only when scripting would add more maintenance than reliability, and make that choice explicit in the skill.
- Update `SKILL.md` to show when to run each script and how to interpret its output.

11. Verify repository context and shared references.
- For skills that operate on a target repository, make `Build repository context first` the first workflow step.
- Ensure that step reads `AGENTS.md`, reads repository-specific docs when they exist, and reads shared docs through the Shared References resolution rule.
- Ensure `Shared References` lists the exact shared standards, knowledge, or package docs used by the skill.
- Ensure direct references to shared docs elsewhere in the skill use the same resolution rule instead of hard-coding only one source.

12. Keep the skill concise with progressive disclosure.
- Keep the top-level workflow readable without loading unnecessary files.
- Assume the agent is already capable; include only non-obvious guidance.
- Move detailed schemas, variants, examples, or long reference material into `references/`.
- Link supporting material directly from `SKILL.md` so it is discoverable without bulk-loading the whole package.

13. Add the OpenAI adapter.
- Add the required `agents/openai.yaml` adapter described by the installed skill standard.
- Keep adapter values aligned with the actual skill scope.
- Regenerate or update the file whenever `SKILL.md` meaning changes.

14. Validate the skill as a package.
- Check that the skill still has a single clear responsibility.
- Check that required sections are present and easy to scan.
- Check that links to shared standards, knowledge, or package docs follow the Shared References resolution rule for runtime use.
- Check that the skill links to shared `standards/` or `knowledge/` instead of copying their policy content.
- Check that deterministic operations are backed by scripts when a script is safer or more repeatable than prose.
- If the environment provides a scaffold or validator for skills, use it; otherwise perform a manual structure and content review.

15. Iterate using realistic tasks.
- Re-test the skill against concrete requests that should trigger it.
- Tighten vague steps, missing prerequisites, or weak guardrails.
- Add supporting files only when the repeated task justifies the extra maintenance.
- Run at most 5 realistic-task iteration passes before stopping and reporting the remaining skill quality gaps.

## Guardrails

- Keep one responsibility per skill and one skill type per skill.
- Do not encode repository-specific behavior as shared truth unless the skill is explicitly repository-specific.
- Do not depend on GitHub URLs or other remote documentation for required execution context when local shared guidance is available.
- Do not hide destructive or high-risk actions inside vague steps.
- Do not add auxiliary files such as `README.md`, `CHANGELOG.md`, or quick-reference notes inside the skill folder unless they are truly required by the runtime.
- Prefer links to shared docs resolved from the installed local package when available over copied policy text.
- Never run more than 5 skill-authoring review iterations before stopping with the remaining gaps.

## Expected Outcome

A reusable shared skill folder with a standards-compliant name, a clear `SKILL.md`, a required `agents/openai.yaml` adapter, and only the supporting files that materially improve correctness, reuse, or maintainability.
