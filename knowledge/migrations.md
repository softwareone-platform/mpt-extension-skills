# Migrations

## Purpose

Describe how to run and create migrations in repositories that support them.

## When To Use This Document

Use this document when you need to:

- run migrations
- create a new migration

## General Approach

This document describes common migration commands that are often available in repositories with a Makefile-based workflow.

## Migration Types

### Schema Migration

A schema migration changes the data structure.

Typical examples:

- create a new table
- add or remove Product parameter
- add new product templates

### Data Migration

A data migration changes the data that already exists.

Typical examples:

- populate a new field for existing records
- migrate values from one format to another
- fulfill new parameters for old agreements/orders
- clean up invalid existing data

## Running Migrations

Use the migration commands documented by the target repository.

Common commands:

```bash
make migrate-check
make migrate-list
make migrate-schema
make migrate-data
```

Typical meaning:

- `make migrate-check`: check migration status
- `make migrate-list`: list available migrations
- `make migrate-schema`: run schema migrations
- `make migrate-data`: run data migrations

If both schema and data migrations must be applied, run them in this order:

1. Apply schema migrations first.
2. Apply data migrations after that.

Typical command sequence:

```bash
make migrate-schema
make migrate-data
```

## How To Create Both Types

Create a schema migration when the structure must change first.

Example:

```bash
make migrate-new-schema name=add_customer_external_id
```

Create a data migration when existing records must be updated.

Example:

```bash
make migrate-new-data name=backfill_customer_external_id
```

## Related Documents

- make targets description `knowledge/make-targets.md`
