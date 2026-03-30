# Common Make Targets

## Purpose

Describe common `make` targets that are frequently used across repositories and explain what they typically mean.

## When To Use This Document

Use this document when you need to:

- understand common `make` target names
- identify the expected purpose of a target in a repository
- navigate a repository that uses a shared Makefile-based workflow

## General Approach

Target names are not guaranteed to exist in every repository, but many repositories use similar names for similar workflows.

Always prefer the target definitions documented by the target repository.

## Common Targets

- `make help`: list available `make` commands
- `make build`: build the local runnable or testable environment
- `make format`: automatically format the source code
- `make check`: run local validation checks such as linting or lock file checks
- `make test`: run the automated test suite
- `make check-all`: run the full local validation flow expected before merge
- `make bash`: open a shell in the application container or runtime environment
- `make shell`: open an application-specific shell, for example a Django shell
- `make review`: run repository-supported review tooling, if available

## Migration-Related Targets

Repositories that support migrations may also expose targets such as:

- `make migrate-check`: check migration status
- `make migrate-list`: list available migrations
- `make migrate-schema`: run schema migrations
- `make migrate-data`: run data migrations
- `make migrate-new-schema name=<migration_id>`: create a new schema migration
- `make migrate-new-data name=<migration_id>`: create a new data migration

## Related Documents

- `standards/makefiles.md`
- `knowledge/build-and-checks.md`
- `knowledge/migrations.md`
