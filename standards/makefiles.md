# Makefile Architecture for Python Repositories

## Owner
Sirius Team

## Scope

Applies to:
 - `Makefile` usage in repositories for extensions, tools, and libraries

## Purpose
Describe the shared `Makefile` approach, its usage, and its structure.

## Make Targets Overview

Common development workflows are wrapped in the `Makefile`. Run `make help` to see the list of available commands.

## How the Makefile Works

The project uses a modular `Makefile` structure that organizes commands into logical groups:

- **Main Makefile** (`Makefile`): entry point that automatically includes all `.mk` files from the `make/` directory
- **Modular includes** (`make/*.mk`): command groups organized by category:
  - `common.mk`: core development commands such as build, test, and format
  - `repo.mk`: repository management and dependency commands
  - `migrations.mk`: database migration commands, available only in extension repositories
  - `external_tools.mk`: integration with external tools

You can extend the `Makefile` with your own custom commands by creating a `local.mk` file inside the `make/` directory. This file should be ignored by Git so personal commands do not affect other developers or appear in version control.
