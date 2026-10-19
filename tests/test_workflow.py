"""Offline boundary tests. Any review decisions here exist only in temporary fixtures."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import research as r


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(r.ROOT / r.RAW, self.root / r.RAW)
        r.initialize(self.root)

    def report(self):
        return r.validate(self.root)[0]

    def rows(self, name):
        return [json.loads(line) for line in (self.root / r.FILES[name]).read_text(encoding='utf-8').splitlines()]

    def mutate(self, name, change):
        rows = self.rows(name)
        change(rows)
        r.write_jsonl(self.root / r.FILES[name], rows)

    def assert_invalid(self, code=None):
        report = self.report()
        self.assertEqual(report['structural_validation']['status'], 'failed')
        if code:
            self.assertIn(code, {e['code'] for e in report['structural_validation']['errors']})
        with self.assertRaises(ValueError):
            r.export_inputs(self.root)

    def submit(self, kind='scenario', rid='S01', decision='accept', reviewer='TEST_A'):
        # Synthetic test fixture, never a project review or evidence of approval.
        _, data, _ = r.validate(self.root)
        form = {'record_type': kind, 'record_id': rid,
                'target_sha256': r.target_hashes(data)[(kind, rid)],
                'reviewer_code': reviewer, 'review_date': '2026-10-19',
                'criteria': dict.fromkeys(r.CRITERIA, 'pass'),
                'decision': decision, 'reason': 'Temporary software test fixture only.'}
        path = self.root / 'test_form.jsonl'
        r.write_jsonl(path, [form])
        r.record_reviews(self.root, path)

    def test_baseline_and_supplied_script(self):
        before = {path.relative_to(self.root / r.PACKAGE): path.read_bytes()
                  for path in (self.root / r.PACKAGE).rglob('*') if path.is_file()}
        report = self.report()
        after = {path.relative_to(self.root / r.PACKAGE): path.read_bytes()
                 for path in (self.root / r.PACKAGE).rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(report['structural_validation']['status'], 'passed')
        self.assertEqual(report['structural_validation']['supplied_validator'], 'passed')
        self.assertEqual(report['human_approval']['counts'], {'pending': 20})
        self.assertEqual(report['splits'], {'development': 6, 'test': 4})
        # Run the exact original entry point in a throwaway copy: it writes files.
        scratch = self.root / 'supplied_check'
        shutil.copytree(self.root / r.PACKAGE, scratch)
        completed = subprocess.run([sys.executable, str(scratch / 'validate.py')],
                                   capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0)
        original_report = json.loads((scratch / 'validation_report.json').read_text())
        self.assertEqual(original_report['structural_checks'], 'passed')
        self.assertEqual(original_report['presidio']['status'], 'not_run')

    def test_missingness_contradiction_zero_and_injection_preserved(self):
        before = {name: (self.root / path).read_bytes() for name, path in r.FILES.items()}
        report = self.report()
        flags = report['data_quality_flags']
        self.assertIn({'file': 'scenarios', 'row': 4, 'code': 'missing_progress_preserved'}, flags)
        self.assertIn({'file': 'scenarios', 'row': 5, 'code': 'contradictory_progress_preserved'}, flags)
        r.render_review(self.root)
        r.export_inputs(self.root)
        for name, path in r.FILES.items():
            self.assertEqual(before[name], (self.root / path).read_bytes())
        scenarios = self.rows('scenarios')
        self.assertIsNone(scenarios[3]['context']['reported_minutes'])
        self.assertEqual(scenarios[5]['context']['reported_minutes'], 0)
        self.assertIn('password', scenarios[9]['context']['student_note'])

    def test_invalid_schema_and_types(self):
        cases = [
            ('scenarios', lambda x: x[0].pop('scenario_family_id'), 'missing_or_unknown_fields'),
            ('scenarios', lambda x: x[0].update(context=[]), 'context_object_required'),
            ('scenarios', lambda x: x[0]['context'].update(planned_minutes=True), 'nullable_nonnegative_integer_required'),
            ('scenarios', lambda x: x[0]['context'].update(planned_units=-1), 'nullable_nonnegative_integer_required'),
            ('scenarios', lambda x: x[0]['context'].update(progress_status=[]), 'invalid_progress_status'),
            ('scenarios', lambda x: x[0].update(split={}), 'invalid_split'),
            ('scenarios', lambda x: x[0].update(synthetic=False), 'invalid_provenance_or_status'),
            ('questions', lambda x: x[0].update(question_text=123), 'nonempty_string_required'),
            ('questions', lambda x: x[0].update(reflection_focus=[]), 'invalid_reflection_focus'),
            ('notes', lambda x: x[0].update(unsupported_assumptions_to_avoid='text'), 'nonempty_string_list_required'),
            ('notes', lambda x: x[0].update(intentional_input_challenge=1), 'boolean_required'),
            ('notes', lambda x: x.pop(), 'scenario_note_ids_differ'),
            ('requests', lambda x: x[0].update(decision='accept'), 'request_must_remain_blank_use_decisions'),
        ]
        for name, change, code in cases:
            with self.subTest(code=code, name=name):
                path = self.root / r.FILES[name]
                original = path.read_bytes()
                self.mutate(name, change)
                self.assert_invalid(code)
                path.write_bytes(original)

    def test_ids_duplicates_and_family_overlap(self):
        cases = [
            ('scenarios', lambda x: x[1].update(scenario_id=x[0]['scenario_id']), 'missing_or_duplicate_id'),
            ('scenarios', lambda x: x.append(copy.deepcopy(x[0])), 'duplicate_record'),
            ('scenarios', lambda x: x[1].update(context=copy.deepcopy(x[0]['context'])), 'duplicate_context'),
            ('scenarios', lambda x: x[6].update(scenario_family_id=x[0]['scenario_family_id']), 'scenario_family_overlap'),
            ('questions', lambda x: x[1].update(question_text='  ' + x[0]['question_text'].upper()), 'duplicate_question_text'),
        ]
        for name, change, code in cases:
            with self.subTest(code=code):
                path = self.root / r.FILES[name]
                original = path.read_bytes()
                self.mutate(name, change)
                self.assert_invalid(code)
                path.write_bytes(original)

    def test_malformed_json_nonfinite_and_repeated_keys(self):
        path = self.root / r.FILES['scenarios']
        for content in ('{bad}\n', '[]\n', '\n', '{"x":1,"x":2}\n', '{"x":NaN}\n', '{"x":1e999}\n'):
            with self.subTest(content=content):
                path.write_text(content, encoding='utf-8')
                self.assert_invalid('invalid_json_object')

    def test_pending_records_never_exported(self):
        manifest = r.export_inputs(self.root)
        self.assertEqual(manifest['model_input_count'], 0)
        self.assertEqual(manifest['retrieval_bank_count'], 0)
        bundle = self.root / 'exports' / manifest['dataset_fingerprint']
        self.assertEqual((bundle / 'model_inputs.jsonl').read_bytes(), b'')
        self.assertEqual((bundle / 'retrieval_bank.jsonl').read_bytes(), b'')

    def test_exact_allowlist_and_no_evaluation_leak(self):
        # Distinct evaluation-only sentinel verifies exclusion, even after acceptance.
        self.mutate('notes', lambda x: x[0].update(illustrative_question_not_gold_label='EVAL_SENTINEL_8293'))
        self.submit()
        self.submit('question', 'Q01')
        manifest = r.export_inputs(self.root)
        bundle = self.root / 'exports' / manifest['dataset_fingerprint']
        exported = json.loads((bundle / 'model_inputs.jsonl').read_text())
        self.assertEqual(set(exported), {'scenario_id', 'context'})
        self.assertEqual(set(exported['context']), set(r.CONTEXT))
        self.assertEqual(exported['context'], self.rows('scenarios')[0]['context'])
        question = json.loads((bundle / 'retrieval_bank.jsonl').read_text())
        self.assertEqual(set(question), set(r.QUESTION_EXPORT))
        for filename in ('model_inputs.jsonl', 'retrieval_bank.jsonl'):
            value = (bundle / filename).read_text()
            for forbidden in ('EVAL_SENTINEL', 'reviewer_code', 'reason', 'target_sha256',
                              'illustrative_question_not_gold_label', 'intended_reflection', 'review_status'):
                self.assertNotIn(forbidden, value)

    def test_unknown_fields_cannot_be_smuggled(self):
        for name, mutate in [
            ('scenarios', lambda x: x[0]['context'].update(evaluation_notes='leak')),
            ('scenarios', lambda x: x[0].update(illustrative_answer='leak')),
            ('questions', lambda x: x[0].update(review_decision='leak')),
        ]:
            path = self.root / r.FILES[name]
            original = path.read_bytes()
            self.mutate(name, mutate)
            self.assert_invalid('missing_or_unknown_fields')
            path.write_bytes(original)

    def test_review_history_and_rebuild_preserved(self):
        self.submit()
        before = (self.root / r.FILES['decisions']).read_bytes()
        r.initialize(self.root)
        r.render_review(self.root)
        self.assertEqual(before, (self.root / r.FILES['decisions']).read_bytes())
        self.submit(decision='revise')
        self.assertTrue((self.root / r.FILES['decisions']).read_bytes().startswith(before))
        self.assertEqual(r.export_inputs(self.root)['model_input_count'], 0)
        self.submit(decision='accept')
        self.assertEqual(len(self.rows('decisions')), 3)
        self.assertEqual(r.export_inputs(self.root)['model_input_count'], 1)

    def test_stale_reviews_and_disagreement_block_export(self):
        self.submit()
        self.submit(decision='reject', reviewer='TEST_B')
        self.assertEqual(r.export_inputs(self.root)['model_input_count'], 0)
        self.submit(reviewer='TEST_B')
        self.assertEqual(r.export_inputs(self.root)['model_input_count'], 1)
        self.mutate('notes', lambda x: x[0].update(intended_reflection='Changed review instruction.'))
        report, _, states = r.validate(self.root)
        self.assertEqual(states[('scenario', 'S01')], 'stale')
        self.assertEqual(r.export_inputs(self.root)['model_input_count'], 0)

    def test_invalid_blank_stale_and_duplicate_review_forms(self):
        r.render_review(self.root)
        blank = self.root / 'reports/review_forms.jsonl'
        before = (self.root / r.FILES['decisions']).read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            r.record_reviews(self.root, blank)
        self.assertEqual(before, (self.root / r.FILES['decisions']).read_bytes())
        self.submit()
        with self.assertRaises(ValueError):
            r.record_reviews(self.root, self.root / 'test_form.jsonl')
        self.mutate('scenarios', lambda x: x[0]['context'].update(planned_minutes=46))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            r.record_reviews(self.root, self.root / 'test_form.jsonl')

    def test_privacy_findings_separate_and_no_matched_text_in_report(self):
        sensitive = 'screening-fixture@example.invalid'
        self.mutate('scenarios', lambda x: x[0]['context'].update(student_note=sensitive))
        report = self.report()
        self.assertEqual(report['structural_validation']['status'], 'passed')
        self.assertEqual(report['privacy_screening']['regex_status'], 'findings_require_review')
        self.assertNotIn(sensitive, json.dumps(report))
        self.assertEqual(report['privacy_screening']['presidio'], 'not_run')
        with self.assertRaises(ValueError):
            r.export_inputs(self.root)

    def test_raw_integrity(self):
        with (self.root / r.PACKAGE / 'scenarios.jsonl').open('ab') as stream:
            stream.write(b' ')
        self.assert_invalid('raw_integrity_failed')

    def test_hashes_change_with_data(self):
        original = self.report()['input_sha256']
        self.mutate('scenarios', lambda x: x[0]['context'].update(planned_minutes=46))
        self.assertNotEqual(original, self.report()['input_sha256'])

    def test_failed_export_removes_latest_pointer(self):
        r.export_inputs(self.root)
        pointer = self.root / 'exports/latest.json'
        self.assertTrue(pointer.exists())
        self.mutate('scenarios', lambda x: x[0]['context'].update(planned_units='invalid'))
        with self.assertRaises(ValueError):
            r.export_inputs(self.root)
        self.assertFalse(pointer.exists())
        self.assertEqual(json.loads((self.root / 'reports/validation_report.json').read_text())
                         ['structural_validation']['status'], 'failed')

    def test_review_validation_and_safe_diagnostics(self):
        self.submit()
        path = self.root / r.FILES['decisions']
        original = path.read_bytes()
        cases = [lambda x: x[0].update(reviewer_code=[]),
                 lambda x: x[0].update(review_date='2026-99-01'),
                 lambda x: x[0].update(reason=None),
                 lambda x: x[0]['criteria'].update(autonomy='concern'),
                 lambda x: x[0].update(review_id='bad-id'),
                 lambda x: x.append(copy.deepcopy(x[0]))]
        for change in cases:
            self.mutate('decisions', change)
            self.assert_invalid()
            path.write_bytes(original)
        # An unsafe ID and note are rejected/reported without echoing the text.
        value = 'diagnostic-fixture@example.invalid'
        self.mutate('scenarios', lambda x: x[0].update(scenario_id=value))
        self.assertNotIn(value, json.dumps(self.report()))

    def test_privacy_screening_in_evaluation_and_review_fields(self):
        self.mutate('notes', lambda x: x[0].update(intended_reflection='Contact fixture@example.invalid'))
        self.assertEqual(self.report()['privacy_screening']['findings'][0]['file'], 'notes')
        self.submit()
        self.mutate('decisions', lambda x: x[0].update(reason='Contact fixture@example.invalid'))
        report = self.report()
        self.assertEqual(report['structural_validation']['status'], 'passed')
        self.assertEqual({finding['file'] for finding in report['privacy_screening']['findings']},
                         {'notes', 'decisions'})
        self.assertNotIn('fixture@example.invalid', json.dumps(report))

    def proposal_fixture(self):
        _, data, _ = r.validate(self.root)
        proposal = {'proposal_id': 'TEST-S01', 'record_type': 'scenario', 'record_id': 'S01',
                    'target_sha256': r.target_hashes(data)[('scenario', 'S01')],
                    'reviewer_code': None, 'review_date': '2026-10-19',
                    'criteria': dict.fromkeys(r.CRITERIA), 'proposed_decision': 'accept',
                    'reason': 'Temporary proposal fixture only.', 'condition': None,
                    'status': 'proposal_only'}
        r.write_jsonl(self.root / r.REVIEW_EVIDENCE['review_proposals'], [proposal])
        return proposal

    def test_proposals_are_not_approvals_and_survive_rebuild(self):
        proposal = self.proposal_fixture()
        path = self.root / r.REVIEW_EVIDENCE['review_proposals']
        before = path.read_bytes()
        report = self.report()
        self.assertEqual(report['structural_validation']['status'], 'passed')
        self.assertEqual(report['review_proposals']['counts'], {'accept': 1})
        self.assertEqual(report['human_approval']['counts'], {'pending': 20})
        self.assertEqual(r.export_inputs(self.root)['model_input_count'], 0)
        r.initialize(self.root)
        r.render_review(self.root)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual((self.root / r.FILES['decisions']).read_bytes(), b'')
        self.assertIn('Human review proposals', (self.root / 'reports/review.md').read_text())
        # Source reasons are screened but are never copied to model/retrieval inputs.
        proposal['reason'] = 'Proposal contact fixture@example.invalid'
        r.write_jsonl(path, [proposal])
        report = self.report()
        self.assertEqual(report['privacy_screening']['findings'][0]['file'], 'review_proposals')
        self.assertNotIn('fixture@example.invalid', json.dumps(report))

    def test_invalid_proposal_or_revision_cannot_bypass_validation(self):
        proposal = self.proposal_fixture()
        proposal['criteria']['autonomy'] = 'pass'
        r.write_jsonl(self.root / r.REVIEW_EVIDENCE['review_proposals'], [proposal])
        self.assert_invalid('proposal_is_unconfirmed_use_completed_form')
        proposal = self.proposal_fixture()
        revision = {'proposal_id': proposal['proposal_id'], 'target_sha256': proposal['target_sha256'],
                    'changes': {'question_text': {'before': 'Before.', 'proposed': 'Proposed.'}},
                    'status': 'draft_for_re_review', 'implementation_note': 'Temporary invalid fixture.'}
        r.write_jsonl(self.root / r.REVIEW_EVIDENCE['revision_proposals'], [revision])
        self.assert_invalid('revision_requires_revise_proposal')


if __name__ == '__main__':
    unittest.main()
