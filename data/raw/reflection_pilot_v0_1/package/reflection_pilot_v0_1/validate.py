"""Offline pilot checks. No network calls, third-party packages or anonymisation.

Usage: python3 validate.py
Optional: python3 validate.py --presidio (requires locally installed packages/model).
"""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_records(name):
    return [json.loads(line) for line in (ROOT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def check(scenarios, questions, reviews):
    errors, flags = [], []
    for records, key in ((scenarios, "scenario_id"), (questions, "question_id"), (reviews, "scenario_id")):
        ids = [r.get(key) for r in records]
        if None in ids or len(ids) != len(set(ids)):
            errors.append(f"Missing or duplicate {key}")
    if {r['scenario_id'] for r in scenarios} != {r['scenario_id'] for r in reviews}:
        errors.append("Scenario/review IDs do not match")
    families = collections.defaultdict(set)
    contexts = set()
    for r in scenarios:
        sid = r['scenario_id']
        families[r['scenario_family_id']].add(r['split'])
        if r['split'] not in {'development', 'test'}:
            errors.append(f"{sid}: invalid split")
        if r.get('synthetic') is not True or r.get('review_status') != 'pending_human_review':
            errors.append(f"{sid}: missing provenance/review declaration")
        c = r['context']
        expected = {'learning_goal', 'planned_activity', 'planned_minutes', 'reported_completed_units', 'planned_units', 'reported_minutes', 'progress_status', 'student_note', 'previous_question'}
        if set(c) != expected:
            errors.append(f"{sid}: unexpected/missing context fields")
        for field in ('learning_goal', 'planned_activity'):
            if not isinstance(c.get(field), str) or not c[field].strip():
                errors.append(f"{sid}: {field} must be a nonempty string")
        for field in ('student_note', 'previous_question'):
            if c.get(field) is not None and not isinstance(c[field], str):
                errors.append(f"{sid}: invalid {field}")
        for field in ('planned_minutes', 'reported_completed_units', 'planned_units', 'reported_minutes'):
            value = c.get(field)
            if value is not None and (type(value) is not int or value < 0):
                errors.append(f"{sid}: invalid {field}")
        if c['progress_status'] not in {'completed', 'partially_completed', 'not_started', 'unknown', 'rescheduled'}:
            errors.append(f"{sid}: invalid progress status")
        text = json.dumps(c, sort_keys=True)
        if text in contexts:
            errors.append(f"{sid}: duplicate context")
        contexts.add(text)
        count, total = c['reported_completed_units'], c['planned_units']
        if count is not None and total is not None and count > total:
            flags.append({'record_id': sid, 'kind': 'count_exceeds_plan', 'action': 'review; do not silently correct'})
        if c['progress_status'] == 'completed' and count is not None and total is not None and count < total:
            flags.append({'record_id': sid, 'kind': 'contradictory_progress', 'action': 'intentional challenge; verify against review notes'})
        if c['progress_status'] == 'unknown':
            flags.append({'record_id': sid, 'kind': 'missing_progress', 'action': 'intentional missingness; do not impute difficulty'})
    for family, splits in families.items():
        if len(splits) > 1:
            errors.append(f"Scenario family crosses splits: {family}")
    qtexts = [r.get('question_text', '').strip().casefold() for r in questions]
    if any(not t for t in qtexts) or len(set(qtexts)) != len(qtexts):
        errors.append('Empty or duplicate question text')
    for r in questions:
        if not all(r.get(k) for k in ('question_id', 'reflection_focus', 'applicable_when', 'avoid_when', 'provenance')):
            errors.append(f"{r.get('question_id')}: incomplete question metadata")
        if r.get('review_status') != 'pending_human_review':
            errors.append(f"{r['question_id']}: human review status not pending")
    # These narrow patterns cannot detect names, addresses or all identifiers.
    patterns = {'email_like': r'\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b', 'phone_like': r'(?<!\w)\+\d[\d ()-]{7,}\d', 'url_like': r'https?://\S+'}
    for r in scenarios + questions:
        rid = r.get('scenario_id', r.get('question_id'))
        for kind, pattern in patterns.items():
            if re.search(pattern, json.dumps(r)):
                flags.append({'record_id': rid, 'kind': kind, 'action': 'manual review required; matched content omitted from report'})
    return errors, flags


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--presidio', action='store_true')
    args = parser.parse_args()
    scenarios = read_records('scenarios.jsonl')
    questions = read_records('question_bank.jsonl')
    reviews = read_records('evaluation_notes.jsonl')
    errors, flags = check(scenarios, questions, reviews)
    pii = {'status': 'not_run', 'reason': 'Optional Presidio scan not requested; regex screening is not a PII audit.'}
    if args.presidio:
        try:
            import spacy
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            # Refuse missing local model rather than trigger a model download.
            if not spacy.util.is_package('en_core_web_lg'):
                raise RuntimeError('Install en_core_web_lg locally before running this scan.')
            engine = NlpEngineProvider(nlp_configuration={'nlp_engine_name': 'spacy', 'models': [{'lang_code': 'en', 'model_name': 'en_core_web_lg'}]}).create_engine()
            analyzer = AnalyzerEngine(nlp_engine=engine, supported_languages=['en'])
            findings = []
            for r in scenarios + questions:
                content = json.dumps(r.get('context', {'question_text': r.get('question_text')}))
                for hit in analyzer.analyze(text=content, language='en', score_threshold=0.5):
                    findings.append({'record_id': r.get('scenario_id', r.get('question_id')), 'entity_type': hit.entity_type, 'score': hit.score})
            pii = {'status': 'completed', 'threshold': 0.5, 'findings': findings, 'limitation': 'Review findings and possible false negatives manually; this is not certification.'}
        except (ImportError, RuntimeError, OSError) as exc:
            pii = {'status': 'not_completed', 'reason': str(exc)}
    report = {'schema_version': '0.1', 'structural_checks': 'passed' if not errors else 'failed', 'errors': errors, 'flags': flags, 'counts': {'scenarios': len(scenarios), 'questions': len(questions), 'splits': dict(collections.Counter(r['split'] for r in scenarios))}, 'presidio': pii, 'human_review': 'pending', 'safety_or_pedagogical_certification': False, 'input_sha256': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('scenarios.jsonl', 'question_bank.jsonl', 'evaluation_notes.jsonl')}}
    (ROOT / 'validation_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    # Export only the explicit allowlisted context to each method; notes never enter this file.
    with (ROOT / 'model_inputs.jsonl').open('w', encoding='utf-8') as f:
        for r in scenarios:
            f.write(json.dumps({'scenario_id': r['scenario_id'], 'context': r['context']}) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if errors or (args.presidio and pii['status'] != 'completed') else 0)


if __name__ == '__main__':
    main()
