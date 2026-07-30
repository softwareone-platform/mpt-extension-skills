import json

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


def test_evaluate_reasons_no_checks_and_no_review():
    result = mod.evaluate({}, mod.DEFAULT_CODERABBIT_LOGINS)
    joined = " | ".join(result["reasons"])
    assert "no status checks found" in joined
    assert "no CodeRabbit review found" in joined


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
