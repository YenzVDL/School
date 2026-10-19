"""Expanded-data boundaries; any decisions written here live in temporary copies."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import research as r


class ExpansionTests(unittest.TestCase):
    def setUp(self):
        previous = r.DATA.name
        r.configure_dataset('exploratory_v0_2')
        self.addCleanup(r.configure_dataset, previous)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for path in (r.RAW, r.DATA, r.REVIEW, Path('data/pilot_v0_1')):
            shutil.copytree(r.ROOT / path, self.root / path)
        # Pending-data tests use a temporary empty decision history, never project approvals.
        (self.root / r.FILES['decisions']).write_bytes(b'')

    def test_counts_coverage_preservation_and_approval(self):
        report, data, _ = r.validate(self.root)
        self.assertEqual(report['structural_validation']['status'], 'passed')
        self.assertEqual(report['structural_validation']['supplied_validator'], 'passed')
        self.assertEqual(report['splits'], {'development':20, 'validation':20, 'test':20})
        self.assertEqual(report['human_approval']['counts'], {'pending':90})
        for counts in report['categories_by_split'].values():
            self.assertEqual(set(counts), r.CATEGORIES)
            self.assertEqual(set(counts.values()), {2})
        self.assertEqual(len(data['questions']), 30)
        self.assertTrue(all(row['split']=='development' for row in data['scenarios'][:10]))
        families = {}
        for row in data['scenarios']:
            families.setdefault(row['scenario_family_id'],set()).add(row['split'])
        self.assertTrue(all(len(splits)==1 for splits in families.values()))
        manifest = json.loads((self.root/r.DATA/'manifest.json').read_text(encoding='utf-8'))
        for name, digest in manifest['file_sha256'].items():
            self.assertEqual(r.sha((self.root/r.DATA/name).read_bytes()), digest)
        before = {path: (self.root/path).read_bytes() for path in r.FILES.values()}
        r.initialize(self.root)
        r.render_review(self.root)
        summary = (self.root/r.REPORTS/'review_summary.md').read_text(encoding='utf-8')
        self.assertIn('| S11 | new |', summary)
        self.assertIn('| S07 | changed: split |', summary)
        self.assertIn('| Q04 | changed: applicable_when |', summary)
        exported = r.export_inputs(self.root)
        self.assertEqual(exported['model_input_count'],0)
        self.assertEqual(exported['retrieval_bank_count'],0)
        for path, content in before.items():
            self.assertEqual((self.root/path).read_bytes(), content)

    def test_validation_test_family_overlap_is_error(self):
        report, data, _ = r.validate(self.root)
        data['scenarios'][30]['split'] = 'test'  # S31 shares F21 with validation S21.
        r.write_jsonl(self.root/r.FILES['scenarios'],data['scenarios'])
        report, _, _ = r.validate(self.root)
        self.assertEqual(report['structural_validation']['status'],'failed')
        self.assertIn('scenario_family_overlap',{e['code'] for e in report['structural_validation']['errors']})
        with self.assertRaises(ValueError):
            r.export_inputs(self.root)

    def test_near_duplicate_flags_do_not_echo_content(self):
        _, data, _ = r.validate(self.root)
        pair = copy.deepcopy(data['scenarios'][20:22])
        pair[1]['context']['learning_goal'] = pair[0]['context']['learning_goal'].upper()
        pair[1]['context']['planned_activity'] = '  ' + pair[0]['context']['planned_activity']
        pair[1]['split'] = 'test'
        flags = r.near_duplicate_flags(pair)
        self.assertEqual(len(flags),1)
        self.assertFalse(flags[0]['same_split'])
        self.assertFalse(flags[0]['same_family'])
        self.assertNotIn(pair[0]['context']['learning_goal'],json.dumps(flags))
        self.assertEqual(flags[0]['sequence_ratio'],1)

    def test_approved_export_still_excludes_all_evaluation_and_review_sources(self):
        _, data, _ = r.validate(self.root)
        data['notes'][20]['illustrative_question_not_gold_label']='EVALUATION_ONLY_SENTINEL_482'
        r.write_jsonl(self.root/r.FILES['notes'],data['notes'])
        targets=r.target_hashes(data)
        forms=[]
        for kind,rid in [('scenario','S21'),('question','Q11')]:
            forms.append(dict(record_type=kind,record_id=rid,target_sha256=targets[(kind,rid)],
                              reviewer_code='TEST_FIXTURE',review_date='2026-10-19',criteria=dict.fromkeys(r.CRITERIA,'pass'),
                              decision='accept',reason='Temporary software fixture, not a project human review.'))
        path=self.root/'test_forms.jsonl'
        r.write_jsonl(path,forms)
        r.record_reviews(self.root,path)
        manifest=r.export_inputs(self.root)
        bundle=self.root/r.EXPORTS/manifest['dataset_fingerprint']
        model=json.loads((bundle/'model_inputs.jsonl').read_text(encoding='utf-8'))
        bank=json.loads((bundle/'retrieval_bank.jsonl').read_text(encoding='utf-8'))
        self.assertEqual(set(model),{'scenario_id','context'})
        self.assertEqual(set(model['context']),set(r.CONTEXT))
        self.assertEqual(set(bank),set(r.QUESTION_EXPORT))
        for filename in ('model_inputs.jsonl','retrieval_bank.jsonl'):
            text=(bundle/filename).read_text(encoding='utf-8')
            for forbidden in ('EVALUATION_ONLY_SENTINEL','reviewer_code','proposed_decision','intended_reflection',
                              'illustrative_question_not_gold_label','review_status','provenance'):
                self.assertNotIn(forbidden,text)


if __name__=='__main__':
    unittest.main()
