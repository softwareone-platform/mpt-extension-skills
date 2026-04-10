# Repository Documentation Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - repositories for extensions, tools, libraries, SDKs, and similar shared components

## Purpose
Define a shared documentation structure and authoring rules that make repository context clear, discoverable, and scalable for both humans and AI agents.

## Definitions

- `Source documentation` is the repository documentation that describes how the repository works, for example `README.md` and files in `docs/`.
- `AI entry point` is the document that tells AI agents how to navigate the repository documentation, normally `AGENTS.md`.
- `Tool-specific adapter` is a thin file required by a specific tool, for example `.github/copilot-instructions.md`, that points to the main repository documentation instead of duplicating it.
- `Shared standard` is a document from the shared `standards/` directory that defines practices reused across multiple repositories.

## General Rules

1. Every repository must expose a predictable documentation structure.
2. Every repository must include this minimal required documentation set:
 - `README.md`
 - `AGENTS.md`
 - `docs/architecture.md`
 - `docs/contributing.md`
 - `docs/testing.md`
3. Additional documents such as `docs/local-development.md`, `docs/deployment.md`, `docs/external-integrations.md`, `docs/e2e.md`, and `docs/migrations.md` should be added when they are relevant to the repository type or runtime model.
4. `README.md` must be the main entry point for humans. It should stay concise and navigational rather than acting as a full reference manual.
5. `AGENTS.md` must be the main entry point for AI agents. It must explain what the repository contains and in which order an agent should read the documentation.
6. `docs/architecture.md` must describe the repository structure, major components, boundaries, and layer responsibilities.
7. `docs/contributing.md` must describe the repository-specific development workflow and reference shared standards instead of duplicating them.
8. `docs/testing.md` must describe the repository-specific testing strategy, test commands, and any special testing constraints or exceptions.
9. Repository documentation must not duplicate shared engineering rules that already exist in shared standards. Repository documents should link to shared standards and document only repository-specific behavior, exceptions, or additional context.
10. Tool-specific adapter files such as `.github/copilot-instructions.md` should remain thin. They should point to `AGENTS.md` or the relevant repository documentation instead of repeating repository policy.
11. Each document should focus on a single topic. Do not mix architecture, setup, testing strategy, and shared policy in one large file unless there is a strong repository-specific reason.
12. Use predictable file names so humans and AI agents can discover information without guessing.
13. Write documentation in explicit and testable language. Prefer `must`, `should`, and `may` over vague wording.
14. Keep examples short, valid, and directly relevant to the rule or workflow they explain.
15. Make the distinction between shared rules and repository-specific rules explicit in every document that references both.

## Recommended Structure

Baseline repository documentation structure:

```text
README.md
AGENTS.md
docs/
  architecture.md
  contributing.md
  testing.md
```

Recommended conditional documents:

```text
docs/
  local-development.md
  deployment.md
  external-integrations.md
  e2e.md
  migrations.md
```

Recommended document responsibilities:

- `README.md`: repository overview, quick start, and links to detailed documentation
- `AGENTS.md`: agent-oriented navigation order and repository reading guidance
- `docs/architecture.md`: system structure, layers, boundaries, and major design decisions
- `docs/contributing.md`: repository-specific workflow, validation commands, and links to shared standards
- `docs/testing.md`: test strategy, test scope, execution commands, and repository-specific constraints
- `docs/local-development.md`: local setup and local execution steps
- `docs/deployment.md`: deployment model, required configuration, and deployment-specific constraints
- `docs/external-integrations.md`: external systems, integration points, and setup expectations
- `docs/e2e.md`: end-to-end test setup, execution, and environment requirements
- `docs/migrations.md`: migration workflow, tooling, and operational guidance
- `docs/documentation.md`: repository documentation guideline, rules

## Authoring Guidance

- Prefer modular documentation over one large document.
- Keep `README.md` short and use it to route readers to more specific documents.
- Keep `AGENTS.md` operational and navigational, not explanatory.
- When a shared standard exists, link to it instead of copying it.
- When repository-specific behavior differs from a shared standard, document the exception explicitly.
- Write documents so a new developer or an AI agent can discover the right next file without additional context.
