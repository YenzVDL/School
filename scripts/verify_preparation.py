"""Run existing/new tests and verify the actual expanded preparation artifacts locally."""
import json
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import research as r


def main():
    root = r.ROOT
    destination = root / 'reports/exploratory_v0_2'
    destination.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                            cwd=root, capture_output=True, text=True, check=False)
    log = result.stdout + result.stderr
    (destination / 'tests.txt').write_text(log, encoding='utf-8')
    print(log)
    matched = re.search(r'Ran (\d+) tests', log)
    summary = {'checked_on': '2026-10-19', 'test_count': int(matched.group(1)) if matched else None,
               'test_status': 'passed' if result.returncode == 0 else 'failed'}
    if result.returncode:
        r.write_json(destination / 'verification.json', summary)
        return result.returncode
    # Verify prior artifacts against hashes recorded before any expansion was written.
    manifest = json.loads((root / 'data/exploratory_v0_2/manifest.json').read_text(encoding='utf-8'))
    preserved = manifest['preserved_source_sha256']
    for name, digest in preserved.items():
        if name.replace('\\','/') == 'data/reviews/decisions.jsonl':
            prefix = (root / 'data/reviews/expanded_pilot_review_20261019/before/data/reviews/decisions.jsonl').read_bytes()
            assert r.sha(prefix) == digest and (root / name).read_bytes().startswith(prefix)
        else:
            assert r.sha((root / name).read_bytes()) == digest
    r.verify_raw(root)
    r.configure_dataset('pilot_v0_1')
    pilot_report, pilot, _ = r.validate(root)
    r.require_valid(pilot_report)
    old_targets = r.target_hashes(pilot)
    applications = r.load_rows(root / 'data/reviews/revision_applications.jsonl', 'applications', [])
    assert len(applications) == 8
    assert all(old_targets[(row['record_type'], row['record_id'])] == row['after_target_sha256'] for row in applications)
    r.configure_dataset('exploratory_v0_2')
    r.initialize(root)
    report, data, states = r.validate(root)
    r.require_valid(report)
    assert len(data['scenarios']) == 60 and len(data['questions']) == 30
    assert report['splits'] == {'development': 20, 'validation': 20, 'test': 20}
    approval_counts = report['human_approval']['counts']
    approved_scenarios = sum(states[('scenario',row['scenario_id'])]=='accepted' for row in data['scenarios'])
    approved_questions = sum(states[('question',row['question_id'])]=='accepted' for row in data['questions'])
    assert all(set(counts.values()) == {2} and set(counts) == r.CATEGORIES for counts in report['categories_by_split'].values())
    families = {split: {row['scenario_family_id'] for row in data['scenarios'] if row['split'] == split}
                for split in r.SPLITS}
    assert all(not families[a] & families[b] for a in families for b in families if a != b)
    duplicates = [flag for flag in report['data_quality_flags'] if flag['code'] == 'possible_near_duplicate_review']
    assert all(flag['same_family'] and flag['same_split'] for flag in duplicates)
    r.render_review(root)
    exported = r.export_inputs(root)
    assert exported['model_input_count'] == approved_scenarios
    assert exported['retrieval_bank_count'] == approved_questions
    forms = r.load_rows(root / r.REPORTS / 'review_forms.jsonl', 'forms', [])
    targets = r.target_hashes(data)
    assert len(forms) == 90 and all(form['decision'] == 'pending' and form['reviewer_code'] is None
                                  and form['criteria'] == dict.fromkeys(r.CRITERIA)
                                  and form['target_sha256'] == targets[(form['record_type'], form['record_id'])] for form in forms)
    assistant = r.load_rows(root / r.REPORTS / 'assistant_review_proposals.jsonl', 'assistant', [])
    assert len(assistant) == 90 and all(row['source'] == 'assistant_preparation' and row['status'] == 'proposed_issues_only' for row in assistant)
    probe = json.loads((root / 'reports/qwen3_8b_setup.json').read_text(encoding='utf-8'))
    config = json.loads((root / 'configs/experiment_v0_2.json').read_text(encoding='utf-8'))
    assert config['model']['selected'] == 'qwen3:8b' and config['model']['artifact_digest'] == probe['model_digest']
    assert config['experiments_enabled'] is False and config['generation']['think'] is False
    run_pointer = root / 'reports/exploratory_v0_2/development_run_latest.json'
    development_run = json.loads(run_pointer.read_text(encoding='utf-8')) if run_pointer.is_file() else None
    summary.update(structural_validation='passed', supplied_validator='passed_with_documented_legacy_split_adapter',
                   preserved_source_files=len(preserved), raw_and_pilot_and_review_history_preserved=True,
                   eight_pilot_revisions_verified=True, scenario_count=60, question_count=30,
                   counts_by_split=report['splits'], categories_by_split=report['categories_by_split'],
                   families_by_split={key: len(value) for key, value in families.items()},
                   near_duplicate_pairs=len(duplicates), cross_split_near_duplicate_pairs=0,
                   human_pending=approval_counts.get('pending',0), approval_counts=approval_counts,
                   completed_decisions=len(data['decisions']), approved_scenario_exports=approved_scenarios,
                   approved_question_exports=approved_questions,
                   review_forms_verified=90, assistant_issue_proposals=90,
                   privacy_screening=report['privacy_screening'], input_sha256=report['input_sha256'],
                   workflow_sha256=report['workflow_sha256'],
                   inference_probe_status=probe['status'], base_model_selected=config['model']['selected'],
                   model_digest=probe['model_digest'], thinking_enabled=False,
                   generic_setup_probe_count=len(probe['probes']),
                   dataset_records_used_for_inference=development_run['summary']['development_scenarios'] if development_run else 0,
                   development_run_executed=bool(development_run),
                   development_model_calls=development_run['summary']['model_calls'] if development_run else 0,
                   comparison_run=bool(development_run), final_comparison_run=False,
                   validation_scenarios_run=0, test_scenarios_run=0, test_frozen=False,
                   review_independence='R01 human review supported by AI-assisted proposals; no independent second review claimed.',
                   open_issues=['Human assessment of development outputs; no quality scores invented.',
                                'Confirm interface fields and pilot-only clarification integration.', 'Review duplicate flags and realism.',
                                'Freeze data, prompts, settings and rubric before final test; authoring assistant has seen all cases.'])
    r.write_json(destination / 'verification.json', summary)
    from scripts.apply_expanded_review import BATCH, verify_application
    if (root / BATCH).exists():
        revision_check = verify_application(root)
        revision_check.update(structural_validation=summary['structural_validation'],
                              tests_passed=summary['test_count'], human_pending=approval_counts.get('pending',0),
                              approved_scenario_exports=approved_scenarios, approved_question_exports=approved_questions,
                              completed_decisions=len(data['decisions']), comparison_run=False)
        r.write_json(destination / 'revision_application_verification.json', revision_check)
    print(f'Preparation verified: 60 scenarios, 30 questions; approval counts {approval_counts}; preserved history.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
