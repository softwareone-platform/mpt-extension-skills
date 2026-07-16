import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-start-jira-work/scripts/analyze_sprint_field.py"
mod = load(SCRIPT_UNDER_TEST)

LEGACY = (
    "com.atlassian.greenhopper.service.sprint.Sprint@1a2b"
    "[id=42,rapidViewId=7,state=ACTIVE,name=Sprint 5, wave 2,startDate=2026-01-01]"
)


def test_classify_state():
    assert mod._classify_state("ACTIVE") == "active"
    assert mod._classify_state(" Closed ") == "closed"
    assert mod._classify_state("future") == "future"
    assert mod._classify_state("weird") == "unknown"
    assert mod._classify_state("") == "unknown"


def test_parse_sprint_entry_object():
    entry = mod.parse_sprint_entry(
        {"id": "3", "name": "S3", "state": "future", "boardId": 9}
    )
    assert entry == {"id": 3, "name": "S3", "state": "future", "board_id": 9}


def test_parse_sprint_entry_object_rapidviewid_fallback():
    entry = mod.parse_sprint_entry({"id": 1, "state": "active", "rapidViewId": 7})
    assert entry["board_id"] == 7


def test_parse_sprint_entry_legacy_string():
    entry = mod.parse_sprint_entry(LEGACY)
    assert entry["id"] == 42
    assert entry["board_id"] == 7
    assert entry["state"] == "active"
    assert entry["name"] == "Sprint 5, wave 2"


def test_parse_sprint_entry_non_numeric_ids():
    entry = mod.parse_sprint_entry({"id": "abc", "state": "active", "boardId": "xyz"})
    assert entry["id"] is None
    assert entry["board_id"] is None


def test_parse_sprint_entry_bad_type():
    try:
        mod.parse_sprint_entry(123)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_analyze_no_sprint_field():
    result = mod.analyze({"issuetype": {"subtask": True}}, "customfield_10020")
    assert result["is_subtask"] is True
    assert result["has_active_sprint"] is False
    assert result["board_ids"] == []
    assert result["sprints"] == []


def test_analyze_mixed_states_and_dedup_boards():
    fields = {
        "issuetype": {"subtask": False},
        "customfield_10020": [
            {"id": 1, "state": "closed", "boardId": 7},
            {"id": 2, "state": "active", "boardId": 7},
            {"id": 3, "state": "future", "boardId": 8},
        ],
    }
    result = mod.analyze(fields, "customfield_10020")
    assert result["has_active_sprint"] is True
    assert result["multiple_active_sprints"] is False
    assert [s["id"] for s in result["closed_sprints"]] == [1]
    assert [s["id"] for s in result["future_sprints"]] == [3]
    assert result["board_ids"] == [7, 8]


def test_analyze_multiple_active():
    fields = {
        "customfield_10020": [
            {"id": 1, "state": "active", "boardId": 7},
            {"id": 2, "state": "active", "boardId": 7},
        ]
    }
    result = mod.analyze(fields, "customfield_10020")
    assert result["multiple_active_sprints"] is True
    assert result["is_subtask"] is False


def test_analyze_rejects_non_list():
    try:
        mod.analyze({"customfield_10020": "nope"}, "customfield_10020")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_main_stdin_full_issue():
    payload = json.dumps(
        {"fields": {"issuetype": {"subtask": False}, "customfield_10020": [LEGACY]}}
    )
    code, out, _ = call_main(mod, [], stdin=payload)
    assert code == 0
    data = json.loads(out)
    assert data["has_active_sprint"] is True
    assert data["board_ids"] == [7]


def test_main_custom_field_id():
    payload = json.dumps({"customfield_99": [{"id": 1, "state": "active", "boardId": 3}]})
    code, out, _ = call_main(mod, ["--sprint-field-id", "customfield_99"], stdin=payload)
    assert code == 0
    assert json.loads(out)["board_ids"] == [3]


def test_main_null_fields_envelope_rejected():
    code, _, err = call_main(mod, [], stdin=json.dumps({"fields": None}))
    assert code == 1
    assert "non-object 'fields'" in err


def test_main_reads_issue_file(tmp_path):
    path = tmp_path / "issue.json"
    path.write_text(json.dumps({"customfield_10020": [{"id": 1, "state": "active", "boardId": 5}]}))
    code, out, _ = call_main(mod, ["--issue-file", str(path)])
    assert code == 0
    assert json.loads(out)["board_ids"] == [5]


def test_main_unreadable_issue_file():
    code, _, err = call_main(mod, ["--issue-file", "/no/such/path.json"])
    assert code == 1
    assert "cannot read" in err


def test_main_invalid_json():
    code, _, err = call_main(mod, [], stdin="{not json")
    assert code == 1
    assert "invalid JSON" in err


def test_main_non_object():
    code, _, err = call_main(mod, [], stdin="[1,2,3]")
    assert code == 1
    assert "expected a JSON object" in err


def test_main_non_list_sprint_field_errors():
    code, _, err = call_main(mod, [], stdin=json.dumps({"customfield_10020": "x"}))
    assert code == 1
    assert "not a list" in err
