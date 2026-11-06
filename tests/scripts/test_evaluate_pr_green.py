import json

import pytest
from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-notify-pr-ready-in-teams/scripts/evaluate_pr_green.py"
mod = load(SCRIPT_UNDER_TEST)


def test_classify_checkrun():
    assert mod.classify_check({"status": "COMPLETED", "conclusion": "SUCCESS"}) == "passing"
    assert mod.classify_check({"status": "COMPLETED", "conclusion": "NEUTRAL"}) == "passing"
    assert mod.classify_check({"status": "COMPLETED", "conclusion": "FAILURE"}) == "failing"
    assert mod.classify_check({"status": "IN_PROGRESS"}) == "pending"
    assert mod.classify_check({"status": "SOMETHING_ELSE"}) == "failing"


def test_classify_status_context():
    assert mod.classify_check({"state": "SUCCESS"}) == "passing"
    assert mod.classify_check({"state": "PENDING"}) == "pending"
    assert mod.classify_check({"state": "ERROR"}) == "failing"
    assert mod.classify_check({}) == "failing"


def test_check_name_fallbacks():
    assert mod._check_name({"name": "tests"}) == "tests"
    assert mod._check_name({"context": "ci"}) == "ci"
    assert mod._check_name({}) == "<unnamed>"


def test_evaluate_checks_states():
    assert mod.evaluate_checks([])["state"] == "none"
    assert mod.evaluate_checks([{"state": "SUCCESS"}])["state"] == "success"
    assert mod.evaluate_checks([{"state": "PENDING"}])["state"] == "pending"
    mixed = mod.evaluate_checks([{"state": "SUCCESS"}, {"state": "ERROR"}, "skip-me"])
    assert mixed["state"] == "failing" and mixed["failing"] == ["<unnamed>"]


def test_latest_reviews_prefers_latest_field():
    payload = {"latestReviews": [{"author": {"login": "x"}, "state": "APPROVED"}]}
    assert mod._latest_reviews(payload)[0]["state"] == "APPROVED"


def test_latest_reviews_from_reviews_keeps_last_per_author():
    payload = {
        "reviews": [
            {"author": {"login": "coderabbitai"}, "state": "COMMENTED"},
            {"author": {"login": "coderabbitai"}, "state": "APPROVED"},
            "junk",
        ]
    }
    reviews = mod._latest_reviews(payload)
    assert len(reviews) == 1 and reviews[0]["state"] == "APPROVED"


def test_latest_reviews_empty_and_invalid():
    assert mod._latest_reviews({}) == []
    assert mod._latest_reviews({"reviews": "nope"}) == []
    assert mod._latest_reviews({"latestReviews": []}) == []


def test_evaluate_coderabbit_variants():
    approved = mod.evaluate_coderabbit(
        {"latestReviews": [{"author": {"login": "coderabbitai"}, "state": "APPROVED"}]},
        mod.DEFAULT_CODERABBIT_LOGINS,
    )
    assert approved["approved"] and approved["found"]

    commented = mod.evaluate_coderabbit(
        {"latestReviews": [{"author": {"login": "coderabbitai"}, "state": "COMMENTED"}]},
        mod.DEFAULT_CODERABBIT_LOGINS,
    )
    assert commented["found"] and not commented["approved"]

    missing = mod.evaluate_coderabbit(
        {"latestReviews": [{"author": {"login": "someone"}, "state": "APPROVED"}]},
        mod.DEFAULT_CODERABBIT_LOGINS,
    )
    assert not missing["found"]


def test_coderabbit_approved_not_masked_by_trailing_commented():
    payload = {
        "reviews": [
            "junk-non-dict-entry",
            {"author": {"login": "someone-else"}, "state": "CHANGES_REQUESTED"},
            {"author": {"login": "coderabbitai"}, "state": "CHANGES_REQUESTED"},
            {"author": {"login": "coderabbitai"}, "state": "COMMENTED"},
            {"author": {"login": "coderabbitai"}, "state": "APPROVED"},
            {"author": {"login": "coderabbitai"}, "state": "COMMENTED"},
        ]
    }
    result = mod.evaluate_coderabbit(payload, mod.DEFAULT_CODERABBIT_LOGINS)
    assert result["state"] == "APPROVED" and result["approved"]


def test_coderabbit_dismissed_after_approved_not_approved():
    payload = {
        "reviews": [
            {"author": {"login": "coderabbitai"}, "state": "APPROVED"},
            {"author": {"login": "coderabbitai"}, "state": "DISMISSED"},
        ]
    }
    result = mod.evaluate_coderabbit(payload, mod.DEFAULT_CODERABBIT_LOGINS)
    assert result["state"] == "DISMISSED" and not result["approved"]


def test_coderabbit_only_commented_found_not_approved():
    payload = {"reviews": [{"author": {"login": "coderabbitai"}, "state": "COMMENTED"}]}
    result = mod.evaluate_coderabbit(payload, mod.DEFAULT_CODERABBIT_LOGINS)
    assert result["found"] and result["state"] == "COMMENTED" and not result["approved"]


def test_evaluate_green_and_reasons():
    green = mod.evaluate(
        {
            "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS", "name": "t"}],
            "latestReviews": [{"author": {"login": "coderabbitai"}, "state": "APPROVED"}],
        },
        mod.DEFAULT_CODERABBIT_LOGINS,
    )
    assert green["is_green"] and green["reasons"] == []

    red = mod.evaluate(
        {
            "statusCheckRollup": [
                {"status": "COMPLETED", "conclusion": "FAILURE", "name": "a"},
                {"state": "PENDING", "context": "b"},
            ],
            "reviews": [{"author": {"login": "coderabbitai"}, "state": "COMMENTED"}],
        },
        mod.DEFAULT_CODERABBIT_LOGINS,
    )
    assert not red["is_green"]
    joined = " | ".join(red["reasons"])
    assert "failing checks: a" in joined
    assert "pending checks: b" in joined
    assert "not APPROVED" in joined


def test_evaluate_reasons_no_checks_and_no_coderabbit_activity():
    result = mod.evaluate({}, mod.DEFAULT_CODERABBIT_LOGINS)

    assert result["reasons"] == ["no status checks found on the PR"]
    assert result["coderabbit"]["required"] is False


def test_main_reads_stdin():
    payload = json.dumps(
        {
            "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
            "latestReviews": [{"author": {"login": "bot"}, "state": "APPROVED"}],
        }
    )
    code, out, _ = call_main(mod, ["--coderabbit-login", "bot"], stdin=payload)
    assert code == 0
    assert json.loads(out)["is_green"] is True


def test_main_invalid_json():
    code, _, err = call_main(mod, [], stdin="{bad")
    assert code == 1
    assert "invalid JSON" in err


def test_main_non_object_json():
    code, _, err = call_main(mod, [], stdin="[]")
    assert code == 1
    assert "expected a JSON object" in err


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({}, {"state": "OPEN", "is_draft": False, "ok": True}),
        ({"state": "OPEN", "isDraft": False}, {"state": "OPEN", "is_draft": False, "ok": True}),
        ({"state": "OPEN", "isDraft": True}, {"state": "OPEN", "is_draft": True, "ok": False}),
        ({"state": "merged"}, {"state": "MERGED", "is_draft": False, "ok": False}),
        ({"state": "CLOSED", "isDraft": True}, {"state": "CLOSED", "is_draft": True, "ok": False}),
    ],
)
def test_evaluate_pr_state(payload, expected):
    result = mod.evaluate_pr_state(payload)

    assert result == expected


def _green_payload(**pr_fields):
    return {
        "statusCheckRollup": [{"state": "SUCCESS"}],
        "latestReviews": [{"author": {"login": "coderabbitai"}, "state": "APPROVED"}],
        **pr_fields,
    }


@pytest.mark.parametrize(
    ("pr_fields", "reasons"),
    [
        ({"state": "MERGED"}, ["PR is MERGED, not OPEN"]),
        ({"state": "CLOSED"}, ["PR is CLOSED, not OPEN"]),
        ({"state": "OPEN", "isDraft": True}, ["PR is a draft"]),
    ],
)
def test_evaluate_not_green_unless_open(pr_fields, reasons):
    result = mod.evaluate(_green_payload(**pr_fields), mod.DEFAULT_CODERABBIT_LOGINS)

    assert result["is_green"] is False
    assert result["reasons"] == reasons


def test_evaluate_green_for_open_pr():
    result = mod.evaluate(
        _green_payload(state="OPEN", isDraft=False), mod.DEFAULT_CODERABBIT_LOGINS
    )

    assert result["is_green"] is True
    assert result["reasons"] == []


@pytest.fixture
def checks_only_payload():
    def factory(**fields):
        return {"statusCheckRollup": [{"state": "SUCCESS"}], **fields}

    return factory


def test_evaluate_green_without_coderabbit_activity(checks_only_payload):
    result = mod.evaluate(checks_only_payload(), mod.DEFAULT_CODERABBIT_LOGINS)

    assert result["is_green"] is True
    assert result["coderabbit"]["required"] is False
    assert result["reasons"] == []


def test_evaluate_requires_coderabbit_when_it_reviewed(checks_only_payload):
    payload = checks_only_payload(
        reviews=[{"author": {"login": "coderabbitai"}, "state": "CHANGES_REQUESTED"}]
    )

    result = mod.evaluate(payload, mod.DEFAULT_CODERABBIT_LOGINS)

    assert result["is_green"] is False
    assert result["coderabbit"]["required"] is True
    assert result["reasons"] == ["CodeRabbit review state is CHANGES_REQUESTED, not APPROVED"]


@pytest.mark.parametrize(
    ("rollup", "expected"),
    [
        ([{"name": "CodeRabbit", "status": "COMPLETED", "conclusion": "SUCCESS"}], True),
        ([{"context": "CodeRabbit", "state": "PENDING"}], True),
        ([{"name": "coderabbit", "status": "IN_PROGRESS"}], True),
        ([{"name": "CodeRabbit", "status": "COMPLETED", "conclusion": "SKIPPED"}], False),
        ([{"name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS"}, "junk"], False),
        (None, False),
    ],
)
def test_coderabbit_check_active(rollup, expected):
    result = mod.coderabbit_check_active(rollup)

    assert result is expected


def test_evaluate_requires_coderabbit_when_its_check_ran():
    payload = {
        "statusCheckRollup": [
            {"name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "CodeRabbit", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ]
    }

    result = mod.evaluate(payload, mod.DEFAULT_CODERABBIT_LOGINS)

    assert result["is_green"] is False
    assert result["coderabbit"]["required"] is True
    assert result["coderabbit"]["check_active"] is True
    assert result["reasons"] == ["no CodeRabbit review found"]


def test_evaluate_green_when_coderabbit_check_skipped():
    payload = {
        "statusCheckRollup": [
            {"name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "CodeRabbit", "status": "COMPLETED", "conclusion": "SKIPPED"},
        ]
    }

    result = mod.evaluate(payload, mod.DEFAULT_CODERABBIT_LOGINS)

    assert result["is_green"] is True
    assert result["coderabbit"]["required"] is False


def test_main_green_without_coderabbit_activity(checks_only_payload):
    code, out, _ = call_main(mod, [], stdin=json.dumps(checks_only_payload()))

    result = json.loads(out)
    assert code == 0
    assert result["is_green"] is True
    assert result["coderabbit"]["required"] is False


def test_main_blocks_non_approved_coderabbit_review(checks_only_payload):
    payload = checks_only_payload(
        reviews=[{"author": {"login": "coderabbitai"}, "state": "CHANGES_REQUESTED"}]
    )

    code, out, _ = call_main(mod, [], stdin=json.dumps(payload))

    result = json.loads(out)
    assert code == 0
    assert result["is_green"] is False
    assert result["coderabbit"]["required"] is True
    assert result["reasons"] == ["CodeRabbit review state is CHANGES_REQUESTED, not APPROVED"]
