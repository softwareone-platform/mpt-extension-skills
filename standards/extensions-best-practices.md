# Extension Best Practices

## Owner
Sirius Team

## Scope

Applies to:
 - MPT extensions

## Purpose
Define shared design and architecture practices for building maintainable, deployable, and reusable MPT extensions.

## Definitions

- `Required external dependencies` are dependencies that are fundamental to the extension behavior and normally cannot be replaced in real environments, for example the MPT API or a Vendor API.
- `Additional external dependencies` are supporting integrations that are not essential for the extension core logic during local development, for example Airtable, Key Vault, or similar systems.

## General Rules

1. An extension should contain only extension-specific business logic. Technical infrastructure code and MPT Marketplace-specific integration code should be isolated behind clear boundaries.
2. An extension should be easy to run in all supported environments:
 - on a cluster
 - on a developer's local machine
 - on Vendor or Client infrastructure
3. An extension should support blue-green deployment.
4. Vendor extensions that process orders must operate only in the Vendor scope. Do not design them in a way that requires Operations or Client account contexts unless there is an explicit documented exception.
5. Design extensions so they can run locally with a minimal number of external dependencies.
6. Keep required external dependencies as real integrations, but design additional external dependencies so they can be replaced with local mocks or local substitutes in the local development environment.
7. The goal of local replacement for additional dependencies is to simplify local development, debugging, and local execution of the extension.
8. Prefer reusable and configurable steps inside an extension.
9. When the same implementation pattern appears in multiple extensions, prefer extracting it into reusable steps or shared libraries.

## Recommended Design Direction

- Separate business logic from transport, framework, and marketplace integration code.
- Prefer dependency injection or adapter-based design for additional external dependencies.
- Keep local development setup lightweight and predictable.
- Design steps so they can be reused across multiple extensions with configuration instead of copy-paste.
