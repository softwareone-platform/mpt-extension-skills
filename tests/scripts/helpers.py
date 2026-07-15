"""Shared helpers for in-process skill-script tests.

Scripts are imported and their ``main()`` is called in-process (rather than
via subprocess) so ``pytest-cov`` can measure line and branch coverage.
"""
import contextlib
import importlib.util
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_MODULE_CACHE: dict[str, object] = {}


def load(relpath: str):
    """Import a skill script as a module (cached)."""
    if relpath in _MODULE_CACHE:
        return _MODULE_CACHE[relpath]
    path = REPO_ROOT / relpath
    name = "skillscript_" + str(abs(hash(relpath)))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _MODULE_CACHE[relpath] = module
    return module


def call_main(module, args: list[str], stdin: str = "") -> tuple[int, str, str]:
    """Call ``module.main()`` with argv/stdin patched; return (code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    old_argv, old_stdin = sys.argv, sys.stdin
    sys.argv = ["prog", *args]
    sys.stdin = io.StringIO(stdin)
    code = 0
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = module.main()
        code = result if isinstance(result, int) else 0
    except SystemExit as exc:  # argparse errors and explicit exits
        code = 0 if exc.code is None else (exc.code if isinstance(exc.code, int) else 1)
    finally:
        sys.argv, sys.stdin = old_argv, old_stdin
    return code, out.getvalue(), err.getvalue()
