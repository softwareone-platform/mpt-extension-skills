import json

import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = (
    "skills/mpt-ext-workflow-coderabbit-review-loop/scripts/evaluate_review_cycle.py"
)
mod = load(SCRIPT_UNDER_TEST)

LOGINS = mod.DEFAULT_CODERABBIT_LOGINS


def _review(state, login="coderabbitai", submitted=None):
    review = {"author": {"login": login}, "state": state}
    if submitted:
        review["submittedAt"] = submitted
    return review


def _thread(first_login="coderabbitai", last_login=None, resolved=False, **fields):
    comments = [{"author": {"login": first_login}, "body": fields.pop("body", "issue")}]
    if last_login:
        comments.append({"author": {"login": last_login}, "body": "follow-up"})
    return {
        "id": fields.pop("id", "T1"),
        "isResolved": resolved,
        "path": fields.pop("path", "src/app.py"),
        "line": fields.pop("line", 10),
        "comments": {"nodes": comments},
        **fields,
    }


def test_parse_iso_timestamp_variants():
    aware = mod.parse_iso_timestamp("2026-09-03T10:00:00Z")
    assert aware.tzinfo is not None
    assert mod.parse_iso_timestamp("2026-09-03T10:00:00z") == aware
    naive = mod.parse_iso_timestamp("2026-09-03T10:00:00")
    assert naive == aware
    with pytest.raises(ValueError):
        mod.parse_iso_timestamp("not-a-date")


def test_evaluate_reviews_approved_not_masked_by_trailing_commented():
    payload = {
        "reviews": [
            "junk",
            _review("CHANGES_REQUESTED"),
            _review("APPROVED"),
            _review("COMMENTED"),
        ]
    }
    result = mod.evaluate_reviews(payload, LOGINS, None)
    assert result["approved"] and result["state"] == "APPROVED"


def test_evaluate_reviews_dismissed_and_missing():
    dismissed = mod.evaluate_reviews(
        {"reviews": [_review("APPROVED"), _review("DISMISSED")]}, LOGINS, None
    )
    assert dismissed["state"] == "DISMISSED" and not dismissed["approved"]

    missing = mod.evaluate_reviews(
        {"reviews": [_review("APPROVED", login="human")]}, LOGINS, None
    )
    assert not missing["found"] and missing["state"] is None


def test_evaluate_reviews_freshness_since():
    since = mod.parse_iso_timestamp("2026-09-03T10:00:00Z")
    payload = {
        "reviews": [
            _review("COMMENTED", submitted="2026-09-03T09:00:00Z"),
            _review("CHANGES_REQUESTED", submitted="2026-09-03T11:00:00Z"),
            _review("COMMENTED", submitted="broken-timestamp"),
            _review("COMMENTED"),
        ]
    }
    result = mod.evaluate_reviews(payload, LOGINS, since)
    assert result["new_review_since"] is True
    assert result["latest_submitted_at"].startswith("2026-09-03T11:00:00")

    stale = mod.evaluate_reviews(
        {"reviews": [_review("COMMENTED", submitted="2026-09-03T10:00:00Z")]},
        LOGINS,
        since,
    )
    assert stale["new_review_since"] is False

    no_since = mod.evaluate_reviews({"reviews": [_review("APPROVED")]}, LOGINS, None)
    assert no_since["new_review_since"] is None


def test_evaluate_reviews_out_of_order_payload_uses_timestamps():
    payload = {
        "reviews": [
            _review("APPROVED", submitted="2026-09-03T11:00:00Z"),
            _review("CHANGES_REQUESTED", submitted="2026-09-03T10:00:00Z"),
        ]
    }
    result = mod.evaluate_reviews(payload, LOGINS, None)
    assert result["approved"] and result["state"] == "APPROVED"
    assert result["decision_submitted_at"].startswith("2026-09-03T11:00:00")


def test_untimestamped_newer_verdict_is_not_outranked():
    """A missing timestamp must not let an older APPROVED win."""
    payload = {
        "reviews": [
            _review("APPROVED", submitted="2026-09-03T11:00:00Z"),
            _review("CHANGES_REQUESTED"),
        ]
    }
    result = mod.evaluate_reviews(payload, LOGINS, None)
    assert result["state"] == "CHANGES_REQUESTED"
    assert not result["approved"]


def test_approval_currency_against_since():
    since = mod.parse_iso_timestamp("2026-09-03T10:00:00Z")
    stale = mod.evaluate_reviews(
        {"reviews": [_review("APPROVED", submitted="2026-09-03T09:00:00Z")]}, LOGINS, since
    )
    assert stale["approved"] and stale["approval_is_current"] is False

    fresh = mod.evaluate_reviews(
        {"reviews": [_review("APPROVED", submitted="2026-09-03T11:00:00Z")]}, LOGINS, since
    )
    assert fresh["approval_is_current"] is True

    no_since = mod.evaluate_reviews({"reviews": [_review("APPROVED")]}, LOGINS, None)
    assert no_since["approval_is_current"] is None

    not_approved = mod.evaluate_reviews(
        {"reviews": [_review("CHANGES_REQUESTED", submitted="2026-09-03T11:00:00Z")]},
        LOGINS,
        since,
    )
    assert not_approved["approval_is_current"] is None


def test_evaluate_cycle_stale_approval_reason():
    since = mod.parse_iso_timestamp("2026-09-03T10:00:00Z")
    result = mod.evaluate_cycle(
        {"reviews": [_review("APPROVED", submitted="2026-09-03T09:00:00Z")]},
        [],
        LOGINS,
        since,
        None,
    )
    assert result["coderabbit"]["approval_is_current"] is False
    assert any("predates" in reason for reason in result["reasons"])


def test_evaluate_reviews_tolerates_malformed_authors():
    payload = {
        "reviews": [
            {"author": "coderabbitai", "state": "APPROVED"},
            {"author": {"login": 42}, "state": "APPROVED"},
            {"author": None, "state": "APPROVED"},
            _review("CHANGES_REQUESTED"),
        ]
    }
    result = mod.evaluate_reviews(payload, LOGINS, None)
    assert result["state"] == "CHANGES_REQUESTED"


def test_review_login_shapes():
    assert mod.review_login({"author": {"login": "CodeRabbitAI"}}) == "coderabbitai"
    assert mod.review_login({"author": "string-author"}) == ""
    assert mod.review_login({"author": {"login": 7}}) == ""
    assert mod.review_login({}) == ""


def test_comment_author_ignores_non_string_logins():
    assert mod.comment_author({"author": {"login": 42}}) == ""
    assert mod.comment_author({"login": 7}) == ""


def test_review_source_fallbacks():
    assert mod._review_source({"reviews": "nope", "latestReviews": [_review("APPROVED")]})
    assert mod._review_source({}) == []
    result = mod.evaluate_reviews({"latestReviews": [_review("APPROVED")]}, LOGINS, None)
    assert result["approved"]


def test_extract_threads_envelopes():
    nodes = [_thread()]
    envelope = {
        "data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": nodes}}}}
    }
    assert mod.extract_threads(envelope) == nodes
    assert mod.extract_threads({"reviewThreads": {"nodes": nodes}}) == nodes
    assert mod.extract_threads({"nodes": nodes}) == nodes
    assert mod.extract_threads(nodes) == nodes
    with pytest.raises(ValueError):
        mod.extract_threads({"unexpected": True})
    with pytest.raises(ValueError):
        mod.extract_threads({"data": {"unexpected": True}})


def test_classify_threads_actionable_and_counts():
    threads = [
        _thread(id="fresh"),
        _thread(id="answered", last_login="agent-user"),
        _thread(id="counter", last_login="coderabbitai"),
        _thread(id="resolved", resolved=True),
        _thread(id="human", first_login="human"),
        "junk",
        {"id": "empty", "isResolved": False, "comments": {"nodes": []}},
    ]
    actionable, unresolved = mod.classify_threads(threads, LOGINS)
    assert [t["id"] for t in actionable] == ["fresh", "counter"]
    assert unresolved == 3


def test_classify_threads_comment_shapes():
    bare_list = {
        "id": "T2",
        "isResolved": False,
        "path": "a.py",
        "line": 1,
        "comments": [{"user": {"login": "coderabbitai"}, "body": "x"}, "junk"],
    }
    simplified = {
        "id": "T3",
        "isResolved": False,
        "path": "b.py",
        "line": 2,
        "comments": {"nodes": [{"author": "coderabbitai[bot]", "body": "y"}]},
    }
    no_comments = {"id": "T4", "isResolved": False, "comments": "nope"}
    actionable, unresolved = mod.classify_threads(
        [bare_list, simplified, no_comments], LOGINS
    )
    assert [t["id"] for t in actionable] == ["T2", "T3"]
    assert unresolved == 2


def test_last_comment_alias_preferred_over_truncated_page():
    comments = {"nodes": [{"author": {"login": "coderabbitai"}, "body": "issue"}]}
    human_last = {
        "id": "T9",
        "isResolved": False,
        "path": "a.py",
        "line": 1,
        "comments": comments,
        "lastComment": {"nodes": [{"author": {"login": "human"}, "body": "done"}]},
    }
    actionable, unresolved = mod.classify_threads([human_last], LOGINS)
    assert unresolved == 1 and actionable == []

    bot_last = dict(
        human_last,
        lastComment={"nodes": [{"author": {"login": "coderabbitai"}, "body": "still"}]},
    )
    actionable, _ = mod.classify_threads([bot_last], LOGINS)
    assert [t["id"] for t in actionable] == ["T9"]
    assert actionable[0]["last_comment_body"] == "still"


def test_last_comment_alias_shapes_and_fallback():
    comments = {"nodes": [{"author": {"login": "coderabbitai"}, "body": "first"}]}
    bare_alias = {
        "id": "T10",
        "isResolved": False,
        "comments": comments,
        "last_comment": [{"author": "coderabbitai", "body": "bare"}],
    }
    actionable, _ = mod.classify_threads([bare_alias], LOGINS)
    assert actionable[0]["last_comment_body"] == "bare"

    junk_alias = {
        "id": "T11",
        "isResolved": False,
        "comments": comments,
        "lastComment": {"nodes": ["junk"]},
    }
    actionable, _ = mod.classify_threads([junk_alias], LOGINS)
    assert actionable[0]["last_comment_body"] == "first"


def test_comment_author_fallbacks():
    assert mod.comment_author({"login": "direct"}) == "direct"
    assert mod.comment_author({"user": "rest-string"}) == "rest-string"
    assert mod.comment_author({"author": {}}) == ""


def test_fingerprint_stability_and_change():
    threads = [
        {"path": "a.py", "line": 1, "last_comment_body": "Fix  THIS "},
        {"path": "b.py", "line": 2, "last_comment_body": "and that"},
    ]
    reordered = list(reversed(threads))
    assert mod.compute_fingerprint(threads) == mod.compute_fingerprint(reordered)
    changed = [dict(threads[0], last_comment_body="different"), threads[1]]
    assert mod.compute_fingerprint(changed) != mod.compute_fingerprint(threads)
    assert mod.compute_fingerprint([]).startswith("sha256:")
    no_body = mod.compute_fingerprint([{"path": "a.py", "line": 1}])
    assert no_body.startswith("sha256:")


def test_evaluate_checks_summary():
    result = mod.evaluate_checks(
        [
            {"status": "COMPLETED", "conclusion": "SUCCESS", "name": "tests"},
            {"status": "IN_PROGRESS", "name": "build"},
            {"state": "ERROR", "context": "lint"},
            "junk",
        ]
    )
    assert result["state"] == "failing"
    assert result["passing"] == ["tests"]
    assert result["pending"] == ["build"]
    assert result["failing"] == ["lint"]
    assert mod.evaluate_checks([])["state"] == "none"
    assert mod.evaluate_checks([{"state": "SUCCESS"}])["state"] == "success"
    assert mod.evaluate_checks([{"state": "PENDING"}])["state"] == "pending"
    assert mod.classify_check({"status": "COMPLETED", "conclusion": "FAILURE"}) == "failing"
    assert mod._check_name({}) == "<unnamed>"


def test_evaluate_cycle_no_progress_and_reasons():
    pr_payload = {"reviews": [_review("CHANGES_REQUESTED")]}
    threads = [_thread()]
    first = mod.evaluate_cycle(pr_payload, threads, LOGINS, None, None)
    assert first["actionable_threads"]["count"] == 1
    assert first["no_progress"] is False
    assert any("not APPROVED" in reason for reason in first["reasons"])

    second = mod.evaluate_cycle(pr_payload, threads, LOGINS, None, first["fingerprint"])
    assert second["no_progress"] is True
    assert any("no progress" in reason for reason in second["reasons"])


def test_evaluate_cycle_no_progress_needs_actionable_threads():
    pr_payload = {"reviews": []}
    empty = mod.evaluate_cycle(pr_payload, [], LOGINS, None, None)
    again = mod.evaluate_cycle(pr_payload, [], LOGINS, None, empty["fingerprint"])
    assert again["no_progress"] is False
    assert any("no CodeRabbit review" in reason for reason in again["reasons"])


def test_evaluate_cycle_approved():
    result = mod.evaluate_cycle(
        {"reviews": [_review("APPROVED")]}, [], LOGINS, None, None
    )
    assert result["coderabbit"]["approved"] is True
    assert any("APPROVED" in reason for reason in result["reasons"])


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_main_happy_path(tmp_path):
    pr_json = _write(
        tmp_path,
        "pr.json",
        {"reviews": [_review("APPROVED", login="bot", submitted="2026-09-03T11:00:00Z")]},
    )
    threads_json = _write(tmp_path, "threads.json", [_thread(first_login="bot")])
    code, out, _ = call_main(
        mod,
        [
            "--pr-json", pr_json,
            "--threads-json", threads_json,
            "--since", "2026-09-03T10:00:00Z",
            "--previous-fingerprint", "sha256:none",
            "--coderabbit-login", "bot",
        ],
    )
    assert code == 0
    result = json.loads(out)
    assert result["coderabbit"]["approved"] is True
    assert result["new_review_since"] is True
    assert result["actionable_threads"]["count"] == 1


def test_main_error_paths(tmp_path):
    pr_json = _write(tmp_path, "pr.json", {"reviews": []})
    threads_json = _write(tmp_path, "threads.json", [])

    code, _, err = call_main(
        mod, ["--pr-json", str(tmp_path / "missing.json"), "--threads-json", threads_json]
    )
    assert code == 1 and "cannot read" in err

    broken = tmp_path / "broken.json"
    broken.write_text("{bad", encoding="utf-8")
    code, _, err = call_main(
        mod, ["--pr-json", pr_json, "--threads-json", str(broken)]
    )
    assert code == 1 and "invalid JSON" in err

    non_object = _write(tmp_path, "list.json", [])
    code, _, err = call_main(
        mod, ["--pr-json", non_object, "--threads-json", threads_json]
    )
    assert code == 1 and "expected a JSON object" in err

    bad_shape = _write(tmp_path, "shape.json", {"unexpected": True})
    code, _, err = call_main(
        mod, ["--pr-json", pr_json, "--threads-json", bad_shape]
    )
    assert code == 1 and "expected review threads" in err

    code, _, err = call_main(
        mod,
        ["--pr-json", pr_json, "--threads-json", threads_json, "--since", "nope"],
    )
    assert code == 1 and "invalid --since" in err


def test_approval_currency_prefers_head_sha():
    approved_new = {
        "reviews": [
            {
                "author": {"login": "coderabbitai"},
                "state": "APPROVED",
                "submittedAt": "2026-09-03T09:00:00Z",
                "commit": {"oid": "head222"},
            }
        ]
    }
    # Stale by clock, but it reviewed the current head: the SHA wins.
    since = mod.parse_iso_timestamp("2026-09-03T10:00:00Z")
    result = mod.evaluate_reviews(approved_new, LOGINS, since, head_sha="head222")
    assert result["approval_is_current"] is True
    assert result["decision_commit_oid"] == "head222"

    # Fresh by clock, but it reviewed the previous head: not current.
    approved_old = {
        "reviews": [
            {
                "author": {"login": "coderabbitai"},
                "state": "APPROVED",
                "submittedAt": "2026-09-03T11:00:00Z",
                "commit": {"oid": "old111"},
            }
        ]
    }
    result = mod.evaluate_reviews(approved_old, LOGINS, since, head_sha="head222")
    assert result["approval_is_current"] is False


def test_approval_currency_unknown_stays_none():
    """A missing timestamp is unknown, not proof of staleness."""
    result = mod.evaluate_reviews(
        {"reviews": [_review("APPROVED")]},
        LOGINS,
        mod.parse_iso_timestamp("2026-09-03T10:00:00Z"),
    )
    assert result["approved"] and result["approval_is_current"] is None


def test_review_commit_oid_shapes():
    assert mod.review_commit_oid({"commit": {"oid": "abc"}}) == "abc"
    assert mod.review_commit_oid({"commit": {"oid": 7}}) is None
    assert mod.review_commit_oid({"commit": "abc"}) is None
    assert mod.review_commit_oid({}) is None


def test_non_string_state_does_not_crash():
    result = mod.evaluate_reviews(
        {"reviews": [{"author": {"login": "coderabbitai"}, "state": 123}]}, LOGINS, None
    )
    assert result["state"] == "" and not result["found"]


def test_extract_threads_rejects_truncated_page():
    envelope = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "abc"},
                        "nodes": [_thread()],
                    }
                }
            }
        }
    }
    with pytest.raises(ValueError, match="paginated"):
        mod.extract_threads(envelope)
    envelope["data"]["repository"]["pullRequest"]["reviewThreads"]["pageInfo"] = {
        "hasNextPage": False
    }
    assert len(mod.extract_threads(envelope)) == 1


def test_evaluate_checks_accepts_graphql_envelope():
    result = mod.evaluate_checks(
        {"nodes": [{"status": "COMPLETED", "conclusion": "FAILURE", "name": "tests"}]}
    )
    assert result["state"] == "failing" and result["failing"] == ["tests"]
    assert mod.evaluate_checks("nonsense")["state"] == "none"
    assert mod.evaluate_checks(None)["state"] == "none"


def test_fingerprint_discriminates_real_coderabbit_bodies():
    """The banner-plus-boilerplate prefix must not make findings collide."""
    banner = "_Functional Correctness_ | _Major_ | _Quick win_"
    boiler = "<details>\n<summary>Supported by static analysis</summary>"
    a = [{"path": "a.py", "line": 10,
          "last_comment_body": f"{banner}\n\n{boiler}\n\n**Fix the null deref.**"}]
    b = [{"path": "a.py", "line": 10,
          "last_comment_body": f"{banner}\n\n{boiler}\n\n**Unrelated race condition.**"}]
    assert mod.compute_fingerprint(a) != mod.compute_fingerprint(b)


def test_fingerprint_survives_line_drift():
    """Force-push shifts lines and nulls them on outdated threads."""
    body = "**Same unchanged finding.**"
    at_42 = [{"path": "a.py", "line": 42, "last_comment_body": body}]
    outdated = [{"path": "a.py", "line": None, "last_comment_body": body}]
    assert mod.compute_fingerprint(at_42) == mod.compute_fingerprint(outdated)


def test_main_accepts_head_sha(tmp_path):
    pr_json = _write(
        tmp_path,
        "pr.json",
        {
            "reviews": [
                {
                    "author": {"login": "coderabbitai"},
                    "state": "APPROVED",
                    "submittedAt": "2026-09-03T11:00:00Z",
                    "commit": {"oid": "head222"},
                }
            ]
        },
    )
    threads_json = _write(tmp_path, "threads.json", [])
    code, out, _ = call_main(
        mod,
        ["--pr-json", pr_json, "--threads-json", threads_json, "--head-sha", "head222"],
    )
    assert code == 0
    result = json.loads(out)
    assert result["coderabbit"]["approval_is_current"] is True
    assert result["decision_commit_oid"] == "head222"


def test_sha_matches_accepts_abbreviated_shas():
    full = "13369fd48758abef012c748190914c40500921f2"
    assert mod.sha_matches(full, "13369fd") is True
    assert mod.sha_matches(full, full) is True
    assert mod.sha_matches(full, "13369FD") is True
    assert mod.sha_matches("13369fd", full) is True
    assert mod.sha_matches(full, "deadbee") is False
    # too short to be meaningful, and missing values, must not match
    assert mod.sha_matches(full, "133") is False
    assert mod.sha_matches(None, full) is False
    assert mod.sha_matches(full, None) is False


def test_approval_currency_accepts_short_head_sha():
    full = "13369fd48758abef012c748190914c40500921f2"
    payload = {
        "reviews": [
            {
                "author": {"login": "coderabbitai"},
                "state": "APPROVED",
                "submittedAt": "2026-09-04T09:00:00Z",
                "commit": {"oid": full},
            }
        ]
    }
    result = mod.evaluate_reviews(payload, LOGINS, None, head_sha="13369fd")
    assert result["approval_is_current"] is True


def _approved_pr(check_entries, oid="head222"):
    return {
        "reviews": [
            {
                "author": {"login": "coderabbitai"},
                "state": "APPROVED",
                "submittedAt": "2026-09-04T10:00:00Z",
                "commit": {"oid": oid},
            }
        ],
        "statusCheckRollup": check_entries,
    }


def test_exit_gate_needs_approval_and_green_checks():
    green = mod.evaluate_cycle(
        _approved_pr([{"status": "COMPLETED", "conclusion": "SUCCESS", "name": "ci"}]),
        [], LOGINS, None, None, head_sha="head222",
    )
    assert green["exit_gate"] == {"ok": True, "reasons": []}
    assert green["checks"]["ok"] is True


def test_exit_gate_blocked_by_failing_checks():
    red = mod.evaluate_cycle(
        _approved_pr([{"status": "COMPLETED", "conclusion": "FAILURE", "name": "ci"}]),
        [], LOGINS, None, None, head_sha="head222",
    )
    assert red["exit_gate"]["ok"] is False
    assert any("failing checks: ci" in r for r in red["exit_gate"]["reasons"])
    assert any("exit gate blocked" in r for r in red["reasons"])


def test_exit_gate_blocked_by_pending_checks():
    pending = mod.evaluate_cycle(
        _approved_pr([{"status": "IN_PROGRESS", "name": "ci"}]),
        [], LOGINS, None, None, head_sha="head222",
    )
    assert pending["exit_gate"]["ok"] is False
    assert any("pending checks: ci" in r for r in pending["exit_gate"]["reasons"])


def test_exit_gate_blocked_when_approval_not_current():
    stale = mod.evaluate_cycle(
        _approved_pr([{"status": "COMPLETED", "conclusion": "SUCCESS"}], oid="old1111"),
        [], LOGINS, None, None, head_sha="head222",
    )
    assert stale["exit_gate"]["ok"] is False
    assert any("current head" in r for r in stale["exit_gate"]["reasons"])


def test_exit_gate_blocked_when_not_approved():
    blocked = mod.evaluate_cycle(
        {"reviews": [_review("CHANGES_REQUESTED")], "statusCheckRollup": []},
        [], LOGINS, None, None,
    )
    assert blocked["exit_gate"]["ok"] is False
    assert any("has not approved" in r for r in blocked["exit_gate"]["reasons"])


def test_absent_checks_do_not_deadlock_the_gate():
    """A repo with no checks configured must still be able to reach approved."""
    result = mod.evaluate_cycle(
        _approved_pr([]), [], LOGINS, None, None, head_sha="head222",
    )
    assert result["checks"]["state"] == "none" and result["checks"]["ok"] is True
    assert result["exit_gate"]["ok"] is True
