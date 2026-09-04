import json
import subprocess
from types import SimpleNamespace

import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = (
    "skills/mpt-ext-workflow-coderabbit-review-loop/scripts/wait_for_coderabbit.py"
)
mod = load(SCRIPT_UNDER_TEST)

LOGINS = mod.DEFAULT_CODERABBIT_LOGINS
SINCE = mod.parse_iso_timestamp("2026-09-03T10:00:00Z")


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(mod, "_monotonic", fake.monotonic)
    monkeypatch.setattr(mod, "_sleep", fake.sleep)
    return fake


def _review(
    state="CHANGES_REQUESTED",
    submitted="2026-09-03T10:05:00Z",
    login="coderabbitai",
    commit_oid=None,
):
    review = {"author": {"login": login}, "state": state, "submittedAt": submitted}
    if commit_oid:
        review["commit"] = {"oid": commit_oid}
    return review


def _queue_fetches(monkeypatch, results):
    remaining = list(results)
    timeouts = []

    def fake_fetch(pr, timeout_seconds=mod.FETCH_TIMEOUT_SECONDS):
        timeouts.append(timeout_seconds)
        item = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(mod, "fetch_pr_snapshot", fake_fetch)
    return timeouts


def test_parse_iso_timestamp_naive_assumed_utc():
    assert mod.parse_iso_timestamp("2026-09-03T10:00:00") == SINCE


def test_latest_review_after_selection():
    payload = {
        "reviews": [
            "junk",
            _review(login="human"),
            _review(submitted=None),
            _review(submitted="broken"),
            _review(submitted="2026-09-03T10:00:00Z"),
            _review(state="commented", submitted="2026-09-03T10:02:00Z"),
            _review(state="APPROVED", submitted="2026-09-03T10:04:00Z"),
        ]
    }
    found = mod.latest_review_after(payload, LOGINS, SINCE)
    assert found["state"] == "APPROVED"
    assert found["submitted_at"].startswith("2026-09-03T10:04:00")


def test_commented_reviews_are_ignored_by_default():
    """CodeRabbit records chat auto-replies as COMMENTED reviews."""
    payload = {"reviews": [_review(state="COMMENTED", submitted="2026-09-03T10:05:00Z")]}
    assert mod.latest_review_after(payload, LOGINS, SINCE) is None
    accepted = mod.latest_review_after(payload, LOGINS, SINCE, accept_commented=True)
    assert accepted["state"] == "COMMENTED"


def test_head_sha_filters_reviews_of_other_commits():
    payload = {
        "reviews": [
            _review(submitted="2026-09-03T10:05:00Z", commit_oid="old1111"),
            _review(state="APPROVED", submitted="2026-09-03T10:06:00Z", commit_oid="new2222"),
        ]
    }
    found = mod.latest_review_after(payload, LOGINS, SINCE, head_sha="new2222")
    assert found["state"] == "APPROVED" and found["commit_oid"] == "new2222"
    assert mod.latest_review_after(payload, LOGINS, SINCE, head_sha="absent1") is None


def test_review_commit_oid_shapes():
    assert mod.review_commit_oid({"commit": {"oid": "abc"}}) == "abc"
    assert mod.review_commit_oid({"commit": {"oid": 7}}) is None
    assert mod.review_commit_oid({"commit": "abc"}) is None
    assert mod.review_commit_oid({}) is None


def test_latest_review_after_tolerates_malformed_authors():
    payload = {
        "reviews": [
            {"author": "coderabbitai", "state": "APPROVED", "submittedAt": "2026-09-03T10:05:00Z"},
            {"author": {"login": 42}, "state": "APPROVED", "submittedAt": "2026-09-03T10:06:00Z"},
            {"author": None, "state": "APPROVED", "submittedAt": "2026-09-03T10:07:00Z"},
            {"state": "APPROVED", "submittedAt": "2026-09-03T10:08:00Z"},
            _review(state="CHANGES_REQUESTED", submitted="2026-09-03T10:09:00Z"),
        ]
    }
    found = mod.latest_review_after(payload, LOGINS, SINCE)
    assert found["state"] == "CHANGES_REQUESTED"


def test_non_string_state_is_skipped_not_crashed():
    payload = {"reviews": [{"author": {"login": "coderabbitai"}, "state": 123,
                            "submittedAt": "2026-09-03T10:05:00Z"}]}
    assert mod.latest_review_after(payload, LOGINS, SINCE) is None


def test_review_login_shapes():
    assert mod.review_login({"author": {"login": "CodeRabbitAI"}}) == "coderabbitai"
    assert mod.review_login({"author": "string-author"}) == ""
    assert mod.review_login({"author": {"login": 7}}) == ""
    assert mod.review_login({}) == ""


def test_poll_survives_malformed_author_payload(clock, monkeypatch):
    _queue_fetches(monkeypatch, [{"reviews": [{"author": "bot", "state": "APPROVED"}]}])
    result = mod.poll("7", SINCE, 0, 90, LOGINS)
    assert result["outcome"] == "timeout"


def test_latest_review_after_none_cases():
    assert mod.latest_review_after({}, LOGINS, SINCE) is None
    assert mod.latest_review_after({"reviews": "nope"}, LOGINS, SINCE) is None
    fallback = {"latestReviews": [_review(submitted="2026-09-03T10:05:00Z")]}
    assert mod.latest_review_after(fallback, LOGINS, SINCE) is not None
    stale = {"reviews": [_review(submitted="2026-09-03T09:59:00Z")]}
    assert mod.latest_review_after(stale, LOGINS, SINCE) is None


def test_poll_immediate_hit(clock, monkeypatch):
    _queue_fetches(monkeypatch, [{"reviews": [_review()]}])
    result = mod.poll("7", SINCE, 540, 90, LOGINS)
    assert result["outcome"] == "new_review"
    assert result["polls"] == 1 and result["errors"] == 0
    assert clock.sleeps == []


def test_poll_hit_on_second_round(clock, monkeypatch):
    _queue_fetches(monkeypatch, [{"reviews": []}, {"reviews": [_review()]}])
    result = mod.poll("7", SINCE, 100, 30, LOGINS)
    assert result["outcome"] == "new_review"
    assert result["polls"] == 2
    assert clock.sleeps == [30]


def test_poll_timeout_caps_last_sleep(clock, monkeypatch):
    timeouts = _queue_fetches(monkeypatch, [{"reviews": []}])
    result = mod.poll("7", SINCE, 60, 45, LOGINS)
    assert result["outcome"] == "timeout"
    assert result["polls"] == 2
    assert clock.sleeps == [45, 15]
    assert timeouts == [60.0, 15.0]


def test_poll_budget_zero_polls_once_with_full_timeout(clock, monkeypatch):
    timeouts = _queue_fetches(monkeypatch, [{"reviews": []}])
    result = mod.poll("7", SINCE, 0, 90, LOGINS)
    assert result["outcome"] == "timeout" and result["polls"] == 1
    assert clock.sleeps == []
    assert timeouts == [mod.FETCH_TIMEOUT_SECONDS]


def test_poll_fetch_timeouts_capped_by_remaining_budget(clock, monkeypatch):
    timeouts = _queue_fetches(monkeypatch, [{"reviews": []}])
    result = mod.poll("7", SINCE, 100, 30, LOGINS)
    assert result["outcome"] == "timeout" and result["polls"] == 4
    assert timeouts == [60.0, 60.0, 40.0, 10.0]


def test_poll_never_fetches_after_budget_is_spent(clock, monkeypatch):
    timeouts = _queue_fetches(monkeypatch, [{"reviews": []}])
    result = mod.poll("7", SINCE, 30, 30, LOGINS)
    assert result["outcome"] == "timeout" and result["polls"] == 1
    assert timeouts == [30.0]
    assert clock.sleeps == [30]


def test_poll_first_fetch_bounded_by_small_budget(clock, monkeypatch):
    timeouts = _queue_fetches(monkeypatch, [{"reviews": [_review()]}])
    result = mod.poll("7", SINCE, 5, 30, LOGINS)
    assert result["outcome"] == "new_review"
    assert timeouts == [5.0]


def test_poll_recovers_after_error(clock, monkeypatch):
    _queue_fetches(
        monkeypatch, [RuntimeError("gh broke"), {"reviews": [_review()]}]
    )
    result = mod.poll("7", SINCE, 100, 10, LOGINS)
    assert result["outcome"] == "new_review"
    assert result["errors"] == 1


def test_poll_reports_error_on_consecutive_failures(clock, monkeypatch):
    """A failure starting after a good poll is an environment blocker, not silence."""
    _queue_fetches(
        monkeypatch,
        [{"reviews": []}, RuntimeError("gh auth expired")],
    )
    result = mod.poll("7", SINCE, 300, 90, LOGINS)
    assert result["outcome"] == "error"
    assert result["consecutive_errors"] >= mod.CONSECUTIVE_ERROR_LIMIT
    assert result["last_error"] == "gh auth expired"


def test_poll_single_transient_error_still_times_out(clock, monkeypatch):
    _queue_fetches(
        monkeypatch,
        [RuntimeError("blip"), {"reviews": []}],
    )
    result = mod.poll("7", SINCE, 300, 90, LOGINS)
    assert result["outcome"] == "timeout"
    assert result["errors"] == 1 and result["consecutive_errors"] == 0


def test_poll_all_errors(clock, monkeypatch):
    _queue_fetches(monkeypatch, [RuntimeError("gh broke")])
    result = mod.poll("7", SINCE, 10, 10, LOGINS)
    assert result["outcome"] == "error"
    assert result["last_error"] == "gh broke"


def _completed(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_fetch_pr_snapshot_success(monkeypatch):
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *a, **k: _completed(stdout=json.dumps({"reviews": []})),
    )
    assert mod.fetch_pr_snapshot("7") == {"reviews": []}


def test_fetch_pr_snapshot_passes_timeout(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        return _completed(stdout=json.dumps({"reviews": []}))

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    mod.fetch_pr_snapshot("7", 12.5)
    assert captured["timeout"] == 12.5


def test_fetch_pr_snapshot_failures(monkeypatch):
    monkeypatch.setattr(
        mod.subprocess, "run", lambda *a, **k: _completed(returncode=1, stderr="boom")
    )
    with pytest.raises(RuntimeError, match="boom"):
        mod.fetch_pr_snapshot("7")

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _completed(returncode=2))
    with pytest.raises(RuntimeError, match="exit code 2"):
        mod.fetch_pr_snapshot("7")

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _completed(stdout="{bad"))
    with pytest.raises(RuntimeError, match="invalid JSON"):
        mod.fetch_pr_snapshot("7")

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _completed(stdout="[]"))
    with pytest.raises(RuntimeError, match="non-object"):
        mod.fetch_pr_snapshot("7")

    def raise_oserror(*a, **k):
        raise OSError("gh missing")

    monkeypatch.setattr(mod.subprocess, "run", raise_oserror)
    with pytest.raises(RuntimeError, match="gh invocation failed"):
        mod.fetch_pr_snapshot("7")

    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd=["gh"], timeout=60)

    monkeypatch.setattr(mod.subprocess, "run", raise_timeout)
    with pytest.raises(RuntimeError, match="gh invocation failed"):
        mod.fetch_pr_snapshot("7")


def test_main_input_validation():
    code, _, err = call_main(mod, ["--pr", "7", "--since", "nope"])
    assert code == 1 and "invalid --since" in err

    code, _, err = call_main(
        mod, ["--pr", "7", "--since", "2026-09-03T10:00:00Z", "--budget-seconds", "-1"]
    )
    assert code == 1 and "budget-seconds" in err

    code, _, err = call_main(
        mod, ["--pr", "7", "--since", "2026-09-03T10:00:00Z", "--interval-seconds", "0"]
    )
    assert code == 1 and "interval-seconds" in err


def test_main_timeout_is_exit_zero(clock, monkeypatch):
    _queue_fetches(monkeypatch, [{"reviews": []}])
    code, out, _ = call_main(
        mod,
        ["--pr", "7", "--since", "2026-09-03T10:00:00Z", "--budget-seconds", "0"],
    )
    assert code == 0
    assert json.loads(out)["outcome"] == "timeout"


def test_main_new_review_with_login_override(clock, monkeypatch):
    _queue_fetches(monkeypatch, [{"reviews": [_review(login="custom-bot")]}])
    code, out, _ = call_main(
        mod,
        [
            "--pr", "7",
            "--since", "2026-09-03T10:00:00Z",
            "--budget-seconds", "0",
            "--coderabbit-login", "custom-bot",
        ],
    )
    assert code == 0
    assert json.loads(out)["outcome"] == "new_review"


def test_main_all_errors_exit_one(clock, monkeypatch):
    _queue_fetches(monkeypatch, [RuntimeError("gh broke")])
    code, out, _ = call_main(
        mod,
        ["--pr", "7", "--since", "2026-09-03T10:00:00Z", "--budget-seconds", "0"],
    )
    assert code == 1
    assert json.loads(out)["outcome"] == "error"


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


def test_head_sha_filter_accepts_short_sha():
    full = "13369fd48758abef012c748190914c40500921f2"
    payload = {"reviews": [_review(state="APPROVED", submitted="2026-09-03T10:06:00Z",
                                   commit_oid=full)]}
    found = mod.latest_review_after(payload, LOGINS, SINCE, head_sha="13369fd")
    assert found["state"] == "APPROVED"
    assert mod.latest_review_after(payload, LOGINS, SINCE, head_sha="deadbee") is None
