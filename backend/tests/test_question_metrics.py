import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend import demo, methods, scenario_generation
from backend.evaluation_jobs import AIJudgment
from backend.main import create_app
from backend.metrics import report
from backend.question_metrics import assess, summarize
from backend.schema import Question
from .conftest import approved_inputs, wait_job


def output(question="Which approach would you try to check your understanding of Python functions?"):
    return {"id": "out-python", "version": 2, "scenario_version_id": "scenario-python-v3", "status": "completed",
            "method": "constrained", "model": "fixture", "tags": [], "attempt_started_at": "fixture",
            "inputs": {"learning_goal": "Learn Python functions", "planned_activity": "Write five Python functions",
                       "progress": {"planned_units": 5, "completed_units": 2, "unit": "functions"}}, "question": question}


def checks(row):
    return {c["name"]: c for c in assess(row)["checks"]}


def test_pair_identity_is_exact_and_diagnostics_never_claim_semantic_quality():
    row = output()
    before = copy.deepcopy(row)
    result = assess(row)
    assert result == assess(row) and row == before
    assert result["output_version"] == 2 and result["scenario_version_id"] == "scenario-python-v3"
    assert result["status"] == "no_flags" and result["semantic_status"] == "Not assessed"
    assert assess(output("Which SQL approach would you try?"))["pair_hash"] != result["pair_hash"]
    changed = copy.deepcopy(row)
    changed["inputs"]["learning_goal"] = "Learn SQL"
    assert assess(changed)["pair_hash"] != result["pair_hash"]


def test_wrong_technology_generic_question_and_unsupported_completion():
    assert checks(output("Which SQL approach would you try?"))["named_technology_grounding"]["value"] is False
    assert checks(output("What would you like to reflect on?"))["lexical_context_anchor"]["value"] is None
    assert checks(output("How did you complete all five Python functions?"))["completion_claim_supported"]["value"] is False
    row = output("How did you complete all five Python functions?")
    row["inputs"]["progress"]["completed_units"] = 5
    assert checks(row)["completion_claim_supported"]["value"] is True
    del row["inputs"]["progress"]
    assert checks(row)["completion_claim_supported"]["value"] is False


def test_control_claim_requires_recorded_question_and_answer_not_ai_inference():
    row = output("What might you revisit after your incorrect answer about Python?")
    row["inputs"]["control_results"] = [{"ai_inferred_assessment": "incorrect"}]
    assert checks(row)["incorrect_answer_claim_supported"]["value"] is False
    row["inputs"]["control_results"] = [{"question": "What does len([]) return?", "student_answer": "1", "recorded_assessment": "incorrect"}]
    assert checks(row)["incorrect_answer_claim_supported"]["value"] is True


def bank_question(identifier, text, priority=0):
    return {**Question(text=text, priority=priority).model_dump(), "id": identifier, "question_id": identifier}


def test_fixed_and_rag_exclude_wrong_technology_and_repeated_question():
    inputs = output()["inputs"]
    bank = [bank_question("sql", "Which SQL approach would help your learning?", 100),
            bank_question("python", "Which Python functions would you like to practice?", 10),
            bank_question("fallback", "What would you like to reflect on about your ICT learning?")]
    assert methods.fixed(inputs, bank)["selected_version_id"] == "python"
    assert "sql" not in [q["version_id"] for q in methods.retrieve(inputs, bank, 3)]
    inputs["previous_question"] = bank[1]["text"]
    assert methods.fixed(inputs, bank)["selected_version_id"] == "fallback"
    with pytest.raises(ValueError, match="No matching question"):
        methods.fixed(inputs, bank[:2])


def test_all_demonstrations_and_import_templates_have_ict_context():
    for row in demo.SCENARIOS:
        assert scenario_generation.check_scope(row["inputs"])
    for row in json.loads(Path("templates/scenarios.json").read_text()):
        assert scenario_generation.check_scope(row["inputs"])
    assert "ICT education only" in methods.SYSTEM
    assert "context_fit" in methods.EVALUATOR_SYSTEM


def test_three_criteria_are_independent_and_legacy_labels_remain_unassessed():
    row = output()
    old = {"output_id": row["id"], "output_version": 2, "source": "human", "role": "primary", "reviewer": "r", "created_at": "1",
           "judgment": {c: {"value": "Yes"} for c in ["usefulness", "correctness"]}}
    quality = report([row], [old], {})["quality"]["human"]["overall"]
    assert quality["both_rate_assessed"] == 1
    assert quality["all_rate_assessed"] is None and quality["criteria"]["context_fit"]["assessed"] == 0
    new = copy.deepcopy(old)
    new["judgment"]["context_fit"] = {"value": "No"}
    quality = report([row], [new], {})["quality"]["human"]["overall"]
    assert quality["all_rate_assessed"] == 0 and quality["all_end_to_end_acceptance"] == 0
    assert "context_fit" not in old["judgment"]
    with pytest.raises(ValidationError):
        AIJudgment.model_validate({c: {"value": "Yes", "explanation": "Reason", "context": "Evidence"} for c in ["usefulness", "correctness"]})


def test_stored_checks_api_and_offline_script_agree(lab, tmp_path):
    s, r, p, jobs = lab
    _, _, _, ds, bank = approved_inputs(r)
    job = jobs.create_experiment({"name": "Fixed checks", "dataset_snapshot_id": ds["id"], "bank_snapshot_id": bank["id"], "methods": ["fixed"]})
    assert wait_job(s, job["id"])["status"] == "completed"
    row = s.all("outputs")[0]
    assert "fixed_question_checks" not in row  # Collection does not evaluate.
    with TestClient(create_app(s, p)) as client:
        result = client.get(f'/api/outputs/{row["id"]}/question-checks')
        assert result.status_code == 200 and result.json() == assess(row)
    source, target = tmp_path / "export.json", tmp_path / "checks.json"
    source.write_text(json.dumps({"outputs": [row]}), encoding="utf-8")
    subprocess.run([sys.executable, "-m", "scripts.score_questions", str(source), "--output", str(target)], check=True)
    from backend.script_evaluation import evaluate
    assert {k:v for k,v in json.loads(target.read_text()).items() if k!="created_at"} == evaluate([row])
    assert not p.calls
