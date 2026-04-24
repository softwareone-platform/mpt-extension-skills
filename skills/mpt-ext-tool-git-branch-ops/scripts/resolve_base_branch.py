#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys


def release_sort_key(branch: str) -> tuple[int, str]:
    suffix = branch.removeprefix("release/")
    match = re.fullmatch(r"(\d+)(?:[.-].*)?", suffix)
    if match:
        return int(match.group(1)), suffix
    return -1, suffix


def is_numeric_release_branch(branch: str) -> bool:
    suffix = branch.removeprefix("release/")
    return bool(re.fullmatch(r"\d+(?:[.-].*)?", suffix))


def list_remote_release_branches(remote_name: str) -> list[str]:
    ref_prefix = f"{remote_name}/"
    result = subprocess.run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname:short)",
            f"refs/remotes/{remote_name}/release/*",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    branches = []
    for line in result.stdout.splitlines():
        ref_name = line.strip()
        if ref_name.startswith(ref_prefix):
            branches.append(ref_name.removeprefix(ref_prefix))
    return branches


def resolve_base_branch(branch_type: str, remote_name: str) -> str:
    if branch_type in {"feature", "bugfix"}:
        return "main"
    if branch_type in {"hotfix", "backport"}:
        release_branches = [
            branch
            for branch in list_remote_release_branches(remote_name)
            if is_numeric_release_branch(branch)
        ]
        if not release_branches:
            raise ValueError(
                f"no remote numeric release/* branches found for {remote_name}"
            )
        return sorted(release_branches, key=release_sort_key)[-1]
    raise ValueError(f"unsupported branch type: {branch_type}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve the base branch for a work branch type."
    )
    parser.add_argument(
        "--branch-type",
        choices=("feature", "bugfix", "hotfix", "backport"),
        required=True,
    )
    parser.add_argument("--remote-name", default="origin")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of only the base branch",
    )
    args = parser.parse_args()

    try:
        base_branch = resolve_base_branch(args.branch_type, args.remote_name)
    except (subprocess.CalledProcessError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(
            {
                "branch_type": args.branch_type,
                "remote_name": args.remote_name,
                "base_branch": base_branch,
            },
            sys.stdout,
        )
        sys.stdout.write("\n")
    else:
        print(base_branch)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
