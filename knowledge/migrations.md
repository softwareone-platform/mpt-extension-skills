# Migrations

## Migration Types

A schema migration changes the data structure; a data migration changes data that already exists. In MPT repositories:

- schema migration examples: create a new table, add or remove a Product parameter, add new product templates
- data migration examples: populate a new field for existing records, fulfill new parameters for old agreements/orders, clean up invalid existing data

## Running Migrations

Use the migration commands documented by the target repository. Common targets:

```bash
make migrate-check   # check migration status
make migrate-list    # list available migrations
make migrate-schema  # run schema migrations
make migrate-data    # run data migrations
```

When both types must be applied, apply schema migrations before data migrations.

## Creating Migrations

```bash
make migrate-new-schema name=add_customer_external_id
make migrate-new-data name=backfill_customer_external_id
```
