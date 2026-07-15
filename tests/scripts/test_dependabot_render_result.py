import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-dependabot-pr-policy-fix/scripts/render_result.py"
mod = load(SCRIPT_UNDER_TEST)


def test_as_list_and_bullets():
    assert mod.as_list(None) == []
    assert mod.as_list("one") == ["one"]
    assert mod.as_list(["a", "b"]) == ["a", "b"]
    assert mod.render_bullet_list([], empty="none") == ["- none"]
    assert mod.render_bullet_list(["x"]) == ["- x"]


def test_normalize_results_shapes():
    assert mod.normalize_results({"results": [{"a": 1}, "skip"]}) == [{"a": 1}]
    assert mod.normalize_results({"number": 1}) == [{"number": 1}]
    assert mod.normalize_results([{"a": 1}, 2]) == [{"a": 1}]
    assert mod.normalize_results(5) == []


def test_render_pr_result_with_skip_and_fields():
    lines = mod.render_pr_result({
        "number": 7, "url": "https://x/pull/7", "skip_reason": "not a dep bump",
        "changed_files": ["uv.lock"], "validation": [{"command": "make check", "status": "pass"}],
        "amended_sha": "abc", "push_result": "forced",
    })
    text = "\n".join(lines)
    assert "PR #7" in text and "Skip reason: not a dep bump" in text
    assert "Amended commit: `abc`" in text and "Push: forced" in text


def test_main_renders_and_empty_errors(tmp_path):
    good = tmp_path / "r.json"
    good.write_text(json.dumps([{"number": 1, "url": "https://x/pull/1", "status": "processed"}]))
    code, out, _ = call_main(mod, ["--results-json", str(good)])
    assert code == 0 and "## Dependabot PR Policy Fix Results" in out and "PR #1" in out

    empty = tmp_path / "e.json"
    empty.write_text("[]")
    assert call_main(mod, ["--results-json", str(empty)])[0] == 1
