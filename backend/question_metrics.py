"""Deterministic diagnostics for an already linked scenario/question pair.

Checks are deliberately separate from human/AI semantic judgments. A passed
lexical check never establishes correctness or educational effectiveness.
"""
import hashlib
import json
import re
from collections import Counter

VERSION = "ict-question-checks-v1"
TECHNOLOGIES = {
    "python": r"\bpython\b", "javascript": r"\bjavascript\b",
    "typescript": r"\btypescript\b", "java": r"\bjava\b",
    "sql": r"\bsql\b", "git": r"\bgit\b", "html": r"\bhtml\b",
    "css": r"\bcss\b", "react": r"\breact\b", "dns": r"\bdns\b",
    "tcp": r"\btcp\b", "uml": r"\buml\b",
}


def technologies(text):
    return {name for name, pattern in TECHNOLOGIES.items() if re.search(pattern, text, re.I)}


def context_text(inputs):
    # A previous reflection question or an inferred assessment is not evidence
    # that a technology belongs to this activity.
    from .schema import prompt_inputs
    clean = prompt_inputs(inputs)
    clean.pop("previous_question", None)
    return json.dumps(clean, ensure_ascii=False)


def unsupported_technologies(inputs, question):
    return sorted(technologies(question) - technologies(context_text(inputs)))


def assess(output):
    from .methods import output_errors, matches, tokens, input_text, compare_predicate
    from .scenario_generation import check_scope, ScopeViolation
    from .schema import prompt_inputs
    inputs = prompt_inputs(output.get("inputs") or {})
    question = output.get("question") or ""
    pair = {"inputs": inputs, "question": question}
    result = {"version": VERSION, "output_id": output.get("id"), "output_version": output.get("version"),
              "scenario_version_id": output.get("scenario_version_id"),
              "pair_hash": hashlib.sha256(json.dumps(pair, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
              "checks": [], "semantic_status": "Not assessed",
              "notice": "Fixed lexical and rule checks only; review suitability, context fit and correctness separately."}
    def add(name, value, evidence):
        result["checks"].append({"name": name, "value": value, "evidence": evidence})
    if not question:
        result["status"] = "not_assessed"
        return result
    errors = output_errors(question, inputs.get("previous_question"))
    add("question_format_and_nonrepetition", not errors, errors)
    try:
        scope = check_scope(inputs)
        add("ict_scenario", True, scope["evidence_fields"])
    except ScopeViolation as exc:
        add("ict_scenario", False, [str(exc)])
    unsupported = unsupported_technologies(inputs, question)
    add("named_technology_grounding", not unsupported, unsupported)
    conditions = output.get("trace", {}).get("conditions")
    add("selected_question_conditions", matches(conditions, inputs) if conditions is not None else None,
        conditions if conditions is not None else "No fixed-bank applicability conditions")
    shared = sorted(set(tokens(question)) & set(tokens(input_text(inputs))))
    add("lexical_context_anchor", True if shared else None, shared or "No shared content words; inspect semantic relevance")
    completion = re.search(r"\b(?:you (?:completed|finished) all|after completing all|your completed (?:activity|task)|how did you (?:complete|finish) all)\b", question, re.I)
    completed = compare_predicate({"left": "progress.completed_units", "op": "gte", "right": "progress.planned_units"}, inputs)
    add("completion_claim_supported", bool(completed) if completion else None,
        inputs.get("progress") if completion else "No supported completion-claim pattern detected")
    incorrect = re.search(r"\b(?:your incorrect answer|you answered incorrectly|you got .*wrong)\b", question, re.I)
    add("incorrect_answer_claim_supported", matches({"control_assessment": "incorrect"}, inputs) if incorrect else None,
        inputs.get("control_results") if incorrect else "No supported incorrect-answer-claim pattern detected")
    assessed = [c for c in result["checks"] if c["value"] is not None]
    result.update(status="flags_found" if any(c["value"] is False for c in assessed) else "no_flags",
                  checked_count=len(assessed), passed_count=sum(c["value"] is True for c in assessed))
    return result


def summarize(outputs):
    rows = [assess(o) for o in outputs]
    return {"version": VERSION, "statuses": dict(Counter(r["status"] for r in rows)), "pairs": rows,
            "notice": "Recomputed using this script version from saved pairs; no model call and no semantic quality score."}
