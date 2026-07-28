import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = (
    "skills/mpt-ext-task-notify-pr-ready-in-teams/scripts/resolve_teams_destination.py"
)
mod = load(SCRIPT_UNDER_TEST)


def test_env_var_for_destination_convention():
    assert mod.env_var_for_destination("team-backend") == "MPT_TEAMS_WEBHOOK_TEAM_BACKEND"
    assert mod.env_var_for_destination(" Team Frontend ") == "MPT_TEAMS_WEBHOOK_TEAM_FRONTEND"


def test_env_var_for_destination_invalid():
    try:
        mod.env_var_for_destination("!!!")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_resolve_override_convention():
    r = mod.resolve("team-backend", None, None, {})
    assert r["source"] == "override"
    assert r["webhook_env"] == "MPT_TEAMS_WEBHOOK_TEAM_BACKEND"
    assert r["resolved"] is False and "not set" in r["reason"]


def test_resolve_override_present_and_explicit_env():
    environ = {"CUSTOM_HOOK": "https://x"}
    r = mod.resolve("weird name", None, "CUSTOM_HOOK", environ)
    assert r["webhook_env"] == "CUSTOM_HOOK"
    assert r["resolved"] is True and r["reason"] is None


def test_resolve_env_default_wins_over_config():
    environ = {"MPT_TEAMS_WEBHOOK_URL": "https://x"}
    r = mod.resolve(None, "team-backend", None, environ)
    assert r["source"] == "env-default"
    assert r["webhook_env"] == "MPT_TEAMS_WEBHOOK_URL"
    assert r["destination"] is None and r["resolved"] is True


def test_resolve_config_default():
    r = mod.resolve(None, "team-backend", None, {})
    assert r["source"] == "config-default"
    assert r["destination"] == "team-backend"
    assert r["webhook_env"] == "MPT_TEAMS_WEBHOOK_TEAM_BACKEND"
    assert r["resolved"] is False


def test_resolve_unresolvable():
    r = mod.resolve(None, None, None, {})
    assert r["resolved"] is False
    assert r["webhook_env"] is None
    assert "no destination" in r["reason"]


def test_main_success_json():
    code, out, _ = call_main(mod, ["--to", "team-backend"])
    assert code == 0
    data = json.loads(out)
    assert data["webhook_env"] == "MPT_TEAMS_WEBHOOK_TEAM_BACKEND"


def test_main_invalid_destination():
    code, _, err = call_main(mod, ["--to", "!!!"])
    assert code == 1
    assert "error:" in err
