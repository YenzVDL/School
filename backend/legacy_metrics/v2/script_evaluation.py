"""Versioned, reproducible batch evaluation. No model, embeddings or AI labels."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from .question_metrics import assess

VERSION = "fixed-rubric-v2-method-blind"
CRITERIA = ["usefulness", "context_fit", "correctness"]
RULES = {
    "usefulness": "One nonrepeated question, <=40 words; reflection/learning/approach/planning cue; no listed coercive wording. These are form and wording rules, not measured educational benefit.",
    "context_fit": "ICT scenario, no unsupported named technology, shared content words with scenario evidence. No lexical anchor is inconclusive. Bank applicability conditions, method and model never affect the score.",
    "correctness": "Check recognized completion/incorrect-answer claims and named technologies against scenario evidence. Unsupported claims are flags. No recognized, testable claim is inconclusive; lack of a flag does not establish truth.",
}
REFLECTION = re.compile(r"\b(?:reflect\w*|learn\w*|approach\w*|strateg\w*|understand\w*|next step|next action|plan\w*|try|practice|practise|revisit|progress|feedback|support|would you|could you|might you)\b", re.I)
PRESSURE = re.compile(r"\b(?:you must|you should have|why (?:didn't|did not) you|you failed|obviously|lazy|stupid)\b", re.I)
ASSUMPTIONS = re.compile(r"\b(?:you (?:fixed|corrected|overcame|struggled|failed)|your (?:frustration|anxiety|failure|success)|after (?:fixing|correcting))\b", re.I)


def implementation_hash():
    root = Path(__file__).parent
    files = ["script_evaluation.py", "question_metrics.py", "methods.py", "schema.py", "scenario_generation.py"]
    return hashlib.sha256(b"".join(name.encode() + b"\0" + (root / name).read_bytes() for name in files)).hexdigest()


def fingerprint(outputs):
    # Grouping metadata affects report identity, but never enters evaluate_pair.
    pairs = [{k: o.get(k) for k in ["id", "version", "scenario_version_id", "inputs", "question", "status", "method", "model", "condition_id", "repetition"]} for o in outputs]
    return hashlib.sha256(json.dumps(sorted(pairs, key=lambda o: o["id"]), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def evaluate_pair(output):
    # Explicit allow-list: the same question and scenario must receive identical
    # results whether selected from a bank, generated with RAG, or by an LLM.
    diagnostic = assess({k: output.get(k) for k in ["id", "version", "scenario_version_id", "inputs", "question"]})
    checks = {c["name"]: c for c in diagnostic["checks"] if c["name"] != "selected_question_conditions"}
    row = {k: diagnostic[k] for k in ["output_id", "output_version", "scenario_version_id", "pair_hash"]}
    row.update(question=output.get("question"), inputs=output.get("inputs"), checks=list(checks.values()), criteria={})
    if output.get("status") != "completed" or not output.get("question"):
        row.update(status="skipped", reason="Execution did not produce a completed question: " + str(output.get("status")))
        return row
    def criterion(name, flags, positives, inconclusive):
        status = "flag" if flags else "pass" if positives else "inconclusive"
        row["criteria"][name] = {"status": status, "evidence": flags or positives or [inconclusive]}
    def failed(names):
        return [{"check": n, "evidence": checks[n]["evidence"]} for n in names if checks[n]["value"] is False]
    def passed(names):
        return [{"check": n, "evidence": checks[n]["evidence"]} for n in names if checks[n]["value"] is True]
    question = output["question"]
    cue = REFLECTION.search(question)
    pressure = PRESSURE.search(question)
    criterion("usefulness", failed(["question_format_and_nonrepetition"]) + ([{"coercive_wording": pressure.group()}] if pressure else []),
              [{"reflection_cue": cue.group()}] if cue else [], "No listed reflection cue; wording cannot be classified by these rules")
    anchors = passed(["lexical_context_anchor"])
    criterion("context_fit", failed(["ict_scenario", "named_technology_grounding"]), anchors,
              "No shared content words with the scenario")
    fact_checks = ["completion_claim_supported", "incorrect_answer_claim_supported", "named_technology_grounding"]
    fact_flags = failed(fact_checks)
    facts = passed(["completion_claim_supported", "incorrect_answer_claim_supported"])
    unhandled = ASSUMPTIONS.search(question)
    if unhandled:
        facts = []
    criterion("correctness", fact_flags, facts,
              "No recognized supported factual claim; broader factual correctness cannot be established by these rules")
    states = [c["status"] for c in row["criteria"].values()]
    row["status"] = "flag" if "flag" in states else "inconclusive" if "inconclusive" in states else "pass"
    from .methods import tokens, input_text
    query = set(tokens(question))
    context = set(tokens(input_text(output.get("inputs") or {})))
    row["measurements"] = {"word_count": len(question.split()), "context_token_precision": len(query & context) / len(query) if query else None,
                           "shared_content_words": sorted(query & context), "format_pass": checks["question_format_and_nonrepetition"]["value"]}
    return row


def aggregate(rows):
    counts = Counter(r["status"] for r in rows)
    criteria = {}
    for name in CRITERIA:
        values = Counter(r["criteria"][name]["status"] for r in rows if name in r["criteria"])
        decisive = values["pass"] + values["flag"]
        criteria[name] = {"evaluated": sum(values.values()), **{k: values[k] for k in ["pass", "flag", "inconclusive"]},
                          "pass_rate_decisive": values["pass"] / decisive if decisive else None,
                          "positive_evidence_rate": values["pass"] / sum(values.values()) if values else None,
                          "decision_coverage": decisive / sum(values.values()) if values else None}
    valid = [r for r in rows if r["status"] != "skipped"]
    overlap = [r["measurements"]["context_token_precision"] for r in valid if r["measurements"]["context_token_precision"] is not None]
    return {"total": len(rows), "evaluated": len(valid), "criteria": criteria,
            "statuses": {k: counts[k] for k in ["pass", "flag", "inconclusive", "skipped"]},
            "format_pass_rate": sum(r["measurements"]["format_pass"] for r in valid) / len(valid) if valid else None,
            "context_token_precision_mean": sum(overlap) / len(overlap) if overlap else None,
            "unique_question_count": len({" ".join((r.get("question") or "").casefold().split()) for r in valid}),
            "all_pass_per_planned": counts["pass"] / len(rows) if rows and any(all(c["status"] != "inconclusive" for c in r["criteria"].values()) for r in valid) else None}


def evaluate(outputs):
    rows = []
    groups = {}
    for o in outputs:
        row = evaluate_pair(o)
        # Only attach the research condition after scoring is complete.
        row.update(method=o.get("method"), model=o.get("model"), condition_id=o.get("condition_id"), repetition=o.get("repetition", 1))
        rows.append(row)
        key = (row["method"] or "unknown", row["model"] or "Not applicable", row["condition_id"] or "")
        groups.setdefault(key, []).append(row)
    def case(row):
        return (row["scenario_version_id"], row["repetition"])
    case_sets = [{case(r) for r in subset if r["scenario_version_id"]} for subset in groups.values()]
    common = set.intersection(*case_sets) if case_sets else set()
    by_condition = [{"method": key[0], "model": key[1], "condition_id": key[2] or None, **aggregate(subset),
                     "matched_cases": aggregate([r for r in subset if case(r) in common])} for key, subset in sorted(groups.items())]
    return {"version": VERSION, "implementation_hash": implementation_hash(), "source": "fixed_scripts", "batch_hash": fingerprint(outputs), "rules": RULES,
            **aggregate(rows), "pairs": rows, "by_condition": by_condition,
            "comparison": {"common_scenario_repetitions": len(common), "condition_count": len(groups),
                           "same_case_sets": bool(case_sets) and all(s == case_sets[0] for s in case_sets),
                           "policy": "Compare matched exact scenario versions and repetitions. All planned cases, including failed outputs, remain in the denominator. Method/model/trace/retrieval/labels never enter the scorer. No automatic winner or overall weighted quality score."},
            "notice": "Pass means the listed rules passed. Inconclusive means rules cannot establish the criterion. These results are not AI judgments or proof of semantic quality."}


def ready(job, outputs):
    return (job.get("kind") == "experiment" and job.get("status") in ["completed", "completed_with_errors"]
            and bool(outputs) and len(outputs) == job.get("total")
            and not any(o.get("status") in ["pending", "running", "evaluating", "interrupted"] for o in outputs))


def save(store, job_id):
    from .store import now, uid
    with store.connect():
        job = store.get("jobs", job_id)
        outputs = [o for o in store.all("outputs") if o["job_id"] == job_id]
        if not ready(job, outputs):
            raise ValueError("Finish collecting every planned output before running fixed metrics")
        existing = job.get("script_assessment")
        if existing and existing["version"] == VERSION and existing.get("implementation_hash") == implementation_hash() and existing["batch_hash"] == fingerprint(outputs):
            return existing
        result = {**evaluate(outputs), "id": uid("script_assessment"), "job_id": job_id, "created_at": now()}
        history = job.get("script_assessment_history", []) + ([existing] if existing else [])
        store.patch("jobs", job_id, script_assessment=result, script_assessment_history=history)
        return result


def report(job, outputs):
    saved = job.get("script_assessment")
    stale = bool(saved and (saved["version"] != VERSION or saved.get("implementation_hash") != implementation_hash() or saved["batch_hash"] != fingerprint(outputs)))
    return {"can_run": ready(job, outputs), "status": "stale" if stale else "completed" if saved else "ready" if ready(job, outputs) else "collecting",
            "result": saved if not stale else None, "version": VERSION, "rules": RULES}
