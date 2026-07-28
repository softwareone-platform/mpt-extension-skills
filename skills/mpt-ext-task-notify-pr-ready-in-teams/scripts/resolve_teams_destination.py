#!/usr/bin/env python3
"""Resolve which environment variable holds the Teams webhook URL to use.

Keeps the secret webhook URL out of git and out of logs: this script never reads
or prints the URL value, only the *name* of the environment variable that holds
it, and whether that variable is currently set.

Resolution precedence (see the skill and its references):

1. ``--to <destination>``   -> explicit per-run override.
2. ``MPT_TEAMS_WEBHOOK_URL`` -> the default environment variable, when set.
3. ``--default-destination`` -> the project default from ``.mpt/notifications.yaml``.

A destination name maps to an environment variable by convention
(``team-backend`` -> ``MPT_TEAMS_WEBHOOK_TEAM_BACKEND``) unless the caller passes
an explicit ``--webhook-env`` override (for a destination whose configured
``webhook_env`` does not follow the convention).
"""
import argparse
import json
import os
import re
import sys


MIN_PYTHON = (3, 12)

DEFAULT_ENV_VAR = "MPT_TEAMS_WEBHOOK_URL"
ENV_PREFIX = "MPT_TEAMS_WEBHOOK_"


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def env_var_for_destination(destination: str) -> str:
    """Map a logical destination name to its conventional env-var name."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", destination.strip()).strip("_").upper()
    if not slug:
        raise ValueError(f"destination {destination!r} does not yield a usable env-var name")
    return ENV_PREFIX + slug


def resolve(to, default_destination, webhook_env_override, environ) -> dict:
    """Resolve the destination and its webhook env-var name by precedence."""
    if to:
        destination = to
        source = "override"
        env_var = webhook_env_override or env_var_for_destination(to)
    elif environ.get(DEFAULT_ENV_VAR, "").strip():
        destination = None
        source = "env-default"
        env_var = DEFAULT_ENV_VAR
    elif default_destination:
        destination = default_destination
        source = "config-default"
        env_var = webhook_env_override or env_var_for_destination(default_destination)
    else:
        return {
            "resolved": False,
            "destination": None,
            "webhook_env": None,
            "source": None,
            "reason": (
                "no destination could be resolved: pass --to, set "
                f"{DEFAULT_ENV_VAR}, or provide --default-destination"
            ),
        }

    present = bool(environ.get(env_var, "").strip())
    return {
        "resolved": present,
        "destination": destination,
        "webhook_env": env_var,
        "source": source,
        "reason": None if present else f"environment variable {env_var} is not set or empty",
    }


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Resolve the Teams webhook environment-variable name for a destination."
    )
    parser.add_argument("--to", help="Explicit destination name (per-run override).")
    parser.add_argument(
        "--default-destination",
        help="Project default destination, e.g. from .mpt/notifications.yaml.",
    )
    parser.add_argument(
        "--webhook-env",
        help="Explicit env-var name override for a non-conventional destination.",
    )
    args = parser.parse_args()

    try:
        result = resolve(args.to, args.default_destination, args.webhook_env, os.environ)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
