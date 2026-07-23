# Jira Custom Field Reference

## Owner
Sirius Team

## Scope

Applies to:
- skills and workflows that read or write MPT Jira custom fields

## Purpose

Provide a single source of truth for the MPT Jira custom-field IDs that skills use, so skills reference this table instead of hardcoding field IDs inline. When the Jira instance changes a field ID, only this file needs updating.

## Custom Fields

These IDs are specific to the SoftwareOne Jira instance (`softwareone.atlassian.net`, project `MPT`).

| Field | ID | Type | Notes |
|---|---|---|---|
| Team | `customfield_10001` | Team | Inherited from the parent when creating a child issue. |
| Sprint | `customfield_10020` | Sprint (array) | Entries carry `boardId`; classify active/closed/future. `acli` has no command to move issues into a sprint, so setting Sprint needs MCP (or the Agile REST move-to-sprint endpoint). |
| Keywords | `customfield_10287` | Labels | For example `dashboard`, `monitoring`. Inherited from the parent where applicable. |
| HitCount | `customfield_10304` | Number | Dashboard failure count. |
| Environment | `customfield_10365` | Option | For example `prod` (option id `10479`). |

## Standard Fields

Standard (non-custom) fields use their documented API names, not custom-field IDs: `summary`, `description`, `components`, `fixVersions`, `parent`, `assignee`, `reporter`, `labels`, `priority`.

## Notes

- The fallback `acli` can set many custom fields at creation via `additionalAttributes`, but has no command to move issues into a **Sprint** and is unreliable for editing custom fields on existing issues. Prefer MCP for the Sprint field and for custom-field edits; see `mpt-ext-tool-jira-workitem-ops` for the MCP-first interface rule.
- Setting the Sprint field is a Jira Software (Agile) operation, not a Platform field edit. Move an issue into a sprint with `POST /rest/agile/1.0/sprint/{sprintId}/issue` (body `{"issues": ["KEY"]}`), not by writing `customfield_10020` through `/rest/api/3/issue`. Reading a board's sprints is available (`GET /rest/agile/1.0/board/{boardId}/sprint`, or `acli jira board list-sprints`); the write is what `acli` lacks. For subtasks, move the parent and the subtask inherits.
- Keep this table in sync with the Jira instance. A field ID that changes in Jira must be updated here, not in individual skills.

## Related Documents

- [skills.md](./skills.md)
