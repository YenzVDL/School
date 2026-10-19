"""Development runner guards; never call a real generator or HTTP endpoint."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
import research as r
import approaches as a
from local_token_budget import QwenAsciiBudget, PIECES
from scripts.run_development import development_material, schedule


class DevelopmentTests(unittest.TestCase):
    def test_shared_review_history_does_not_invalidate_preserved_pilot(self):
        previous = r.DATA.name
        try:
            r.configure_dataset('pilot_v0_1')
            report, data, states = r.validate(r.ROOT)
            self.assertEqual(report['structural_validation']['status'],'passed')
            self.assertEqual(len(data['decisions']),90)
            self.assertEqual(len(states),20)
            # Changed expanded scenario hashes never authorize earlier pilot scenarios.
            self.assertNotEqual(states[('scenario','S07')],'accepted')
        finally:
            r.configure_dataset(previous)
    def test_only_approved_development_contexts_reach_engine(self):
        config = a.load_config()
        material, data, report = development_material(r.ROOT, config)
        ids = {row['scenario_id'] for row in data['scenarios'] if row['split']=='development'}
        self.assertEqual(len(ids),20)
        self.assertEqual(set(material.contexts),ids)
        self.assertEqual(material.known_scenarios,ids)
        self.assertEqual(len(material.bank),30)
        self.assertEqual(report['human_approval']['counts'],{'accepted':90})
        engine = a.ApproachEngine(material,config)
        for method in ('fixed','rag','direct'):
            self.assertEqual(engine.run('S21',method)['status'],'unknown_scenario')
            self.assertEqual(engine.run('S41',method)['status'],'unknown_scenario')
        prepared = engine.prepare('S01','rag')['request']
        for forbidden in ('illustrative_question_not_gold_label','intended_reflection','reviewer_code',
                          'proposed_criteria','scenario_family_id','"split"','"category"'):
            self.assertNotIn(forbidden,prepared.payload_json)

    def test_pending_development_is_refused_before_any_backend(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for path in (r.RAW,r.REVIEW,Path('data/exploratory_v0_2')):
                shutil.copytree(r.ROOT/path,root/path)
            (root/'data/reviews/decisions.jsonl').write_bytes(b'')
            with self.assertRaisesRegex(ValueError,'require_current_approval'):
                development_material(root,a.load_config())

    def test_fixed_once_and_equal_seed_repetitions_without_heldout_ids(self):
        config = a.load_config()
        ids = {'S01','S02'}
        jobs = schedule(ids,config)
        self.assertEqual(len(jobs),14)
        self.assertTrue(all(rid in ids for rid,_,_ in jobs))
        for rid in ids:
            self.assertEqual([seed for row,method,seed in jobs if row==rid and method=='fixed'],[None])
            for method in ('rag','direct'):
                self.assertEqual({seed for row,m,seed in jobs if row==rid and m==method},set(config['generation']['seeds']))
        self.assertEqual(jobs,schedule(ids,config))

    def test_ascii_bpe_merges_and_budget_fail_closed(self):
        info = {'tokenizer.ggml.pre':'qwen2','tokenizer.ggml.model':'gpt2',
                'tokenizer.ggml.add_bos_token':False,'tokenizer.ggml.merges':['h e','he l','hel l','hell o']}
        budget = QwenAsciiBudget(info)
        self.assertEqual(budget.count('hello'),1)
        sample = 'JSON: {"question_text":"Ready?"}\n/no_think'
        self.assertEqual(''.join(PIECES.findall(sample)),sample)
        request = a.GenerationRequest('fixture','f'*64,'hello','hello',{'num_ctx':2048,'num_predict':128},180)
        self.assertEqual(budget.check(request),66)
        with self.assertRaises(ValueError):
            budget.count('non-ASCII: é')
        with self.assertRaises(a.ContextOverflowError):
            budget.check(a.GenerationRequest('fixture','f'*64,'1'*2048,'hello',request.options,180))


if __name__=='__main__':
    unittest.main()
