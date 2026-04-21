---
name: mpt-ext-workflow-skill-authoring
description: Create or update reusable shared skills when users ask to design, add, refactor, or improve an agent skill. Use this workflow to classify the skill as tool, task, or workflow, apply the shared naming and structure rules, keep the skill concise and reusable, add required agents/openai.yaml metadata, and separate skill-specific behavior from shared standards or knowledge.
---

# Skill Authoring

## Purpose

Create or update a reusable shared skill while treating the installed shared standards and knowledge as the source of truth.

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
- Access to the installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

- Any related shared policy or workflow docs that the skill should reference instead of duplicating.

## Shared References

Read these installed documents before making substantial skill changes:

- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/skills.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/documentation.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/docs/installation.md`

When working inside the source repository rather than an installed package, the equivalent repo-local paths are:

- [../../standards/skills.md](../../standards/skills.md)
- [../../standards/documentation.md](../../standards/documentation.md)
- [../../docs/installation.md](../../docs/installation.md)

## Workflow

1. Understand the intended reuse.
- Identify the repeatable outcome the skill should support.
- Ask for or infer 1-3 concrete example requests that should trigger the skill.
- Stop if the work is clearly a one-off instruction rather than a reusable skill.

2. Decide what belongs in the skill.
- Move cross-repository policy into local `standards/` documents.
- Move reusable how-to or operational guidance into local `knowledge/` documents.
- Keep only the reusable execution behavior that an agent should apply directly inside the skill.

3. Classify the skill before naming it.
- Use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/skills.md` as the source of truth for skill type, naming, required sections, structure, and anti-patterns.
- Choose exactly one skill type and keep the responsibility narrow.

4. Resolve shared package links from the installed root.
- Use the installed package root defined by the skill standard:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

- Build links to shared `standards/`, `knowledge/`, and `docs/` from that root for runtime use.
- Use repo-local fallback links only when the task is explicitly happening inside the source repository.

5. Name the skill with the shared convention.
- Apply the naming convention from the installed skill standard instead of restating it locally.
- Make the folder name exactly match the skill name.

6. Plan the minimum useful structure.
- Follow the required and optional structure from the installed skill standard.
- Add only the supporting directories that materially improve correctness, reuse, or maintainability.

7. Write `SKILL.md` for fast execution.
- Keep frontmatter limited to `name` and `description`.
- Make the description do the trigger work: say what the skill does and when to use it.
- Write the body in direct operational language.
- Include every required section defined by the installed skill standard.
- Use imperative instructions and short concrete examples.

8. Keep the skill concise with progressive disclosure.
- Keep the top-level workflow readable without loading unnecessary files.
- Assume the agent is already capable; include only non-obvious guidance.
- Move detailed schemas, variants, examples, or long reference material into `references/`.
- Link supporting material directly from `SKILL.md` so it is discoverable without bulk-loading the whole package.

9. Add the OpenAI adapter.
- Add the required `agents/openai.yaml` adapter described by the installed skill standard.
- Keep adapter values aligned with the actual skill scope.
- Regenerate or update the file whenever `SKILL.md` meaning changes.

10. Validate the skill as a package.
- Check that the skill still has a single clear responsibility.
- Check that required sections are present and easy to scan.
- Check that links to shared standards, knowledge, or package docs resolve through installed local package paths for runtime use.
- Check that the skill links to shared `standards/` or `knowledge/` instead of copying their policy content.
- If the environment provides a scaffold or validator for skills, use it; otherwise perform a manual structure and content review.

11. Iterate using realistic tasks.
- Re-test the skill against concrete requests that should trigger it.
- Tighten vague steps, missing prerequisites, or weak guardrails.
- Add supporting files only when the repeated task justifies the extra maintenance.

## Guardrails

- Keep one responsibility per skill and one skill type per skill.
- Do not encode repository-specific behavior as shared truth unless the skill is explicitly repository-specific.
- Do not depend on GitHub URLs or other remote documentation for required execution context.
- Do not hide destructive or high-risk actions inside vague steps.
- Do not add auxiliary files such as `README.md`, `CHANGELOG.md`, or quick-reference notes inside the skill folder unless they are truly required by the runtime.
- Prefer links to installed local shared docs over copied policy text.

## Expected Outcome

A reusable shared skill folder with a standards-compliant name, a clear `SKILL.md`, a required `agents/openai.yaml` adapter, and only the supporting files that materially improve correctness, reuse, or maintainability.
