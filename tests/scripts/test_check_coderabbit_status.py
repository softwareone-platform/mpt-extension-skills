import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = (
    "skills/mpt-ext-workflow-coderabbit-review-loop/scripts/check_coderabbit_status.py"
)
mod = load(SCRIPT_UNDER_TEST)


def test_operational_when_up_and_no_incidents():
    result = mod.classify_status({"page": {"name": "CodeRabbit", "status": "UP"}})
    assert result["operational"] is True
    assert result["page_status"] == "UP"
    assert result["reasons"] == []


def test_not_operational_when_page_has_issues():
    result = mod.classify_status({"page": {"status": "HASISSUES"}})
    assert result["operational"] is False
    assert "HASISSUES" in result["reasons"][0]


def test_active_incident_blocks_operational_even_when_up():
    result = mod.classify_status(
        {
            "page": {"status": "UP"},
            "activeIncidents": [
                {"name": "Reviews delayed", "status": "INVESTIGATING"},
                "junk-entry",
            ],
        }
    )
    assert result["operational"] is False
    assert result["active_incidents"] == [
        {"name": "Reviews delayed", "status": "INVESTIGATING"}
    ]
    assert "active incident: Reviews delayed (INVESTIGATING)" in result["reasons"]


def test_maintenance_is_listed_and_page_status_decides():
    result = mod.classify_status(
        {
            "page": {"status": "UNDERMAINTENANCE"},
            "activeMaintenances": [{"name": "DB upgrade", "status": "INPROGRESS"}],
        }
    )
    assert result["operational"] is False
    assert result["active_maintenances"] == [{"name": "DB upgrade", "status": "INPROGRESS"}]


def test_missing_or_empty_page_status():
    missing = mod.classify_status({})
    assert missing["page_status"] is None
    assert missing["operational"] is False
    assert "no page status" in missing["reasons"][0]

    empty = mod.classify_status({"page": {"status": ""}})
    assert empty["page_status"] is None


def test_entry_fallback_names():
    result = mod.classify_status({"page": {"status": "UP"}, "activeIncidents": [{}]})
    assert result["active_incidents"] == [{"name": "<unnamed>", "status": "UNKNOWN"}]


def test_lowercase_page_status_is_normalized():
    result = mod.classify_status({"page": {"status": "up"}})
    assert result["page_status"] == "UP"
    assert result["operational"] is True


def test_main_reads_stdin():
    payload = json.dumps({"page": {"status": "UP"}})
    code, out, _ = call_main(mod, [], stdin=payload)
    assert code == 0
    assert json.loads(out)["operational"] is True


def test_main_invalid_json():
    code, _, err = call_main(mod, [], stdin="{bad")
    assert code == 1
    assert "invalid JSON" in err


def test_main_non_object_json():
    code, _, err = call_main(mod, [], stdin="[]")
    assert code == 1
    assert "expected the Instatus summary" in err
