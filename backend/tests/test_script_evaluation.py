import copy
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend import script_evaluation as scripts
from backend.main import create_app
from .conftest import approved_inputs, wait_job


def output(identifier="o1", method="fixed", question="Which approach would you try to understand Python functions?", scenario="sv1"):
    return {"id": identifier, "version": 1, "scenario_version_id": scenario, "method": method, "model": None if method == "fixed" else "fixture",
            "condition_id": method, "repetition": 1, "status": "completed", "question": question,
            "inputs": {"learning_goal": "Understand Python functions", "planned_activity": "Write five Python functions",
                       "progress": {"planned_units": 5, "completed_units": 2, "unit": "functions"}}}


def test_identical_question_and_context_score_identically_for_every_method_and_model():
    expected = scripts.evaluate_pair(output())
    for method in ["fixed", "rag", "constrained"]:
        row = output(method=method)
        row.update(model="DIFFERENT MODEL", trace={"conditions": {"missing": ["learning_goal"]}, "retrieved": [{"score": 1}]},
                   labels={"usefulness": "Yes"}, priority=999, tags=["approved"], settings={"temperature": 2})
        assert scripts.evaluate_pair(row) == expected
    assert "selected_question_conditions" not in str(expected)


def test_rule_examples_and_unknowns_are_not_silently_passed():
    normal = scripts.evaluate_pair(output())
    assert normal["criteria"]["reflection_structure"]["status"] == "pass"
    assert normal["criteria"]["contextual_grounding"]["status"] == "pass"
    assert normal["criteria"]["factual_grounding"]["status"] == "inconclusive"
    unrelated = scripts.evaluate_pair(output(question="Which SQL approach would you try?"))
    assert unrelated["criteria"]["contextual_grounding"]["status"] == "flag"
    contradicted = scripts.evaluate_pair(output(question="How did you complete all five Python functions?"))
    assert contradicted["criteria"]["factual_grounding"]["status"] == "flag"
    supported = output(question="How did you complete all five Python functions?")
    supported["inputs"]["progress"]["completed_units"] = 5
    assert scripts.evaluate_pair(supported)["criteria"]["factual_grounding"]["status"] == "pass"
    assert scripts.evaluate_pair(output(question="What would you like to reflect on?"))["criteria"]["contextual_grounding"]["status"] == "inconclusive"


def test_comparison_uses_same_cases_and_keeps_failures_in_denominator():
    rows = [output(f"{method}-{n}", method, scenario=f"sv{n}") for method in ["fixed", "rag", "constrained"] for n in [1, 2]]
    rows[-1].update(status="failed", question=None)
    result = scripts.evaluate(rows)
    assert result["evaluated"] == 5 and result["statuses"]["skipped"] == 1
    assert result["comparison"]["common_scenario_repetitions"] == 2
    assert result["comparison"]["same_case_sets"]
    for group in result["by_condition"]:
        assert group["total"] == group["matched_cases"]["total"] == 2
    assert next(g for g in result["by_condition"] if g["method"] == "constrained")["evaluated"] == 1
    rows.append(output("fixed-extra", "fixed", scenario="extra"))
    result = scripts.evaluate(rows)
    assert not result["comparison"]["same_case_sets"]
    assert all(g["matched_cases"]["total"] == 2 for g in result["by_condition"])


def test_same_batch_offline_matches_api_and_old_assessment_is_preserved(lab, tmp_path):
    s, r, p, jobs = lab
    *_, ds, bank = approved_inputs(r)
    job = jobs.create_experiment({"name": "Script comparison", "dataset_snapshot_id": ds["id"], "bank_snapshot_id": bank["id"], "methods": ["fixed", "rag", "constrained"], "models": ["test-fixture-model"]})
    assert wait_job(s, job["id"])["status"] == "completed"
    assert len(p.calls) == 2 and not s.all("labels")  # Generators only.
    p.generate = lambda *a, **kw: pytest.fail("Assessment must never call a model")
    with TestClient(create_app(s, p)) as client:
        initial = client.get(f'/api/jobs/{job["id"]}/metrics').json()
        assert initial["script_evaluation"]["status"] == "ready"
        result = client.post(f'/api/jobs/{job["id"]}/script-evaluation', json={})
        assert result.status_code == 200
        first = result.json()
        assert first["evaluated"] == 3
        assert client.post(f'/api/jobs/{job["id"]}/script-evaluation', json={}).json() == first
        exported = client.get(f'/api/jobs/{job["id"]}/export').json()
        source, target = tmp_path / "export.json", tmp_path / "metrics.json"
        source.write_text(json.dumps(exported), encoding="utf-8")
        subprocess.run([sys.executable, "-m", "scripts.score_questions", str(source), "--output", str(target)], check=True)
        offline = json.loads(target.read_text())
        assert {k:v for k,v in offline.items() if k!="created_at"} == {k: v for k, v in first.items() if k not in ["id", "job_id", "created_at"]}
        row = s.all("outputs")[0]
        s.patch("outputs", row["id"], question="What would you like to reflect on about Python?")
        assert client.get(f'/api/jobs/{job["id"]}/metrics').json()["script_evaluation"]["status"] == "stale"
        second = client.post(f'/api/jobs/{job["id"]}/script-evaluation', json={}).json()
        assert second["id"] != first["id"]
        assert s.all("script_assessments") == [first,second]
        assert "script_assessment" not in s.get("jobs",job["id"])
    assert not s.all("labels")


def test_resume_and_worker_cannot_restart_historical_ai_evaluation(lab):
    s, r, p, jobs = lab
    historical = {"id": "old-eval", "kind": "evaluation", "name": "Historical evaluation", "status": "interrupted", "config": {}, "active_seconds": 0}
    s.put("jobs", historical)
    with pytest.raises(ValueError, match="AI evaluation is disabled"):
        jobs.resume(historical["id"])
    s.patch("jobs", historical["id"], status="queued")
    jobs._run(historical["id"])
    assert s.get("jobs", historical["id"])["status"] == "failed" and not p.calls


def test_offline_script_rejects_partial_export(tmp_path):
    row = output(); row["status"] = "pending"
    source = tmp_path / "partial.json"
    source.write_text(json.dumps({"outputs": [row]}))
    result = subprocess.run([sys.executable, "-m", "scripts.score_questions", str(source)], capture_output=True, text=True)
    assert result.returncode != 0 and "Collection is incomplete" in result.stderr
