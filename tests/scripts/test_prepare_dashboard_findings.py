import json

import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-workflow-dashboard-failure-triage/scripts/prepare_dashboard_findings.py"
mod = load(SCRIPT_UNDER_TEST)


def test_text_helpers():
    assert mod.clean_key('﻿"Foo" ') == "Foo"
    assert mod.compact_text("a   b\n\nc") == "a b c"
    assert mod.tail_lines("l1\nl2\nl3", limit=2) == "l2\nl3"


def test_first_value_and_samples():
    row = {"﻿cloud_RoleName": "svc", "sample_order_ids": '["o1","o2","o3","o4"]', "operation_Id": "op", "empty": None}
    assert mod.first_value(row, "cloud_RoleName") == "svc"
    assert mod.first_value(row, "missing") == ""
    # first_sample: json list -> first element
    assert mod.first_sample(row, "sample_order_ids") == "o1"
    # first_sample: non-json -> raw value
    assert mod.first_sample({"x": "plain"}, "x") == "plain"
    assert mod.first_sample({"x": ""}, "x") == ""
    # sample_values: json list joined with limit
    assert mod.sample_values(row, "sample_order_ids") == "o1, o2, o3"
    # sample_values: non-list json -> str
    assert mod.sample_values({"x": "5"}, "x") == "5"
    # sample_values: plain text
    assert mod.sample_values({"x": "not json"}, "x") == "not json"


def test_failure_title_variants():
    assert "TimeoutError" in mod.failure_title({"any_message": "System.TimeoutError: took too long"})
    assert mod.failure_title({"type": "HttpError", "any_masked_url": "https://x/y"}).startswith("HttpError on ")
    assert mod.failure_title({}) == "Unknown dashboard failure"


def test_normalize_row_failure_count_parsing():
    ok = mod.normalize_row(1, {"cloud_RoleName": "svc", "failures_count": "12"})
    assert ok["failures_count"] == 12
    bad = mod.normalize_row(2, {"cloud_RoleName": "svc", "failures_count": "n/a"})
    assert bad["failures_count"] == 0


def test_load_appinsights_json_list(tmp_path):
    p = tmp_path / "a.json"
    p.write_text(json.dumps([{"cloud_RoleName": "svc", "operation_Id": "op"}]))
    rows = mod.load_appinsights_json(p)
    assert rows == [{"cloud_RoleName": "svc", "operation_Id": "op"}]


def test_load_appinsights_json_tables(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"tables": [{"columns": [{"name": "cloud_RoleName"}, {"name": "x"}], "rows": [["svc", "1"]]}]}))
    rows = mod.load_appinsights_json(p)
    assert rows[0]["cloud_RoleName"] == "svc"


def test_load_appinsights_json_value_and_bad(tmp_path):
    p = tmp_path / "v.json"
    p.write_text(json.dumps({"value": [{"cloud_RoleName": "svc"}]}))
    assert mod.load_appinsights_json(p)[0]["cloud_RoleName"] == "svc"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"unknown": 1}))
    with pytest.raises(ValueError):
        mod.load_appinsights_json(bad)


def test_load_csv(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text("cloud_RoleName,operation_Id\nsvc,op\n")
    rows = mod.load_csv(p)
    assert rows[0]["cloud_RoleName"] == "svc"


def test_normalize_row_and_table():
    row = mod.normalize_row(1, {"cloud_RoleName": "svc", "operation_Id": "op", "any_message": "boom"})
    assert row["cloud_RoleName"] == "svc"
    assert "title" in row
    assert mod.markdown_table([row]).count("|") > 2


def test_main_json_and_markdown(tmp_path):
    src = tmp_path / "f.json"
    src.write_text(json.dumps([{"cloud_RoleName": "b", "operation_Id": "o2"}, {"cloud_RoleName": "a", "operation_Id": "o1"}]))
    code, out, _ = call_main(mod, [str(src), "--format", "json"])
    assert code == 0
    data = json.loads(out)
    assert len(data) == 2 and data[0]["cloud_RoleName"] == "a"  # sorted by role

    code, out, _ = call_main(mod, [str(src)])
    assert code == 0 and "|" in out
