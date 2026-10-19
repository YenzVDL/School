"""AI-rating identity, scenario weighting and versioned prompt guards. No inference."""
import copy
import json
from pathlib import Path
import unittest
import research as r
import approaches as a
from scripts.assess_development import aggregate, verify_ratings, rows

ASSESSMENT = r.ROOT/'data/assessments/development_original_AI01_20261019'


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        manifest=json.loads((ASSESSMENT/'intake_manifest.json').read_text())
        self.run=r.ROOT/manifest['source_run']
        self.ratings=rows(ASSESSMENT/'development_ratings.jsonl')
        self.review=(self.run/'output_review.md').read_bytes()
        self.assessment=(ASSESSMENT/'Development_Assessment.md').read_text(encoding='utf-8')
        self.outputs=[{key:row[key] for key in ('scenario_id','question_text')}
                      for row in rows(self.run/'results.jsonl')]

    def test_all_locked_rating_identities_and_original_files_remain_exact(self):
        checked=verify_ratings(self.ratings,self.review,self.assessment,self.outputs)
        self.assertEqual(checked['verified_review_ids'],140)
        manifest=json.loads((ASSESSMENT/'intake_manifest.json').read_text())
        for name,digest in manifest['source_files_sha256'].items():
            self.assertEqual(r.sha((ASSESSMENT/name).read_bytes()),digest)
        for name,digest in manifest['original_run_files_sha256'].items():
            self.assertEqual(r.sha((self.run/name).read_bytes()),digest)

    def test_missing_duplicate_or_wrong_rating_identities_are_rejected(self):
        candidates=[self.ratings[:-1],self.ratings[:-1]+self.ratings[:1]]
        for field,value in [('scenario_id','S41'),('question','Changed fixture?'),('question_sha256','0'*64)]:
            changed=copy.deepcopy(self.ratings)
            changed[0][field]=value
            candidates.append(changed)
        for candidate in candidates:
            with self.subTest(first=candidate[0]['review_id']):
                with self.assertRaises(ValueError):
                    verify_ratings(candidate,self.review,self.assessment,self.outputs)

    def test_aggregation_weights_scenarios_not_trials_and_separates_safety(self):
        joined=[]
        for method in ('fixed','rag','direct'):
            # Unequal artificial trial counts make pooled and scenario means differ.
            for scenario,scores,repeats in [('S01',0,3),('S02',2,1)]:
                for index in range(repeats):
                    joined.append(dict(method=method,scenario_id=scenario,
                        scores=dict.fromkeys(('specificity','usefulness','clarity','non_coerciveness'),scores),
                        issue_tags=['fixture_issue'] if scenario=='S01' else [],
                        unsupported_assumption=scenario=='S01',observed_serious_safety_failure=False))
        scenarios,methods=aggregate(joined)
        for stats in methods.values():
            self.assertEqual(stats['criterion_means']['usefulness'],1)
            self.assertEqual(stats['unsupported_assumptions']['outputs'],3)
            self.assertEqual(stats['unsupported_assumptions']['scenarios_affected'],1)
            self.assertEqual(stats['unsupported_assumptions']['mean_within_scenario_rate'],0.5)
            self.assertEqual(stats['observed_serious_safety_failures']['outputs'],0)
            self.assertNotIn('overall_score',stats)

    def test_one_shared_prompt_append_preserves_every_other_setting(self):
        original=a.load_config()
        revised=a.load_config(r.ROOT/'configs/experiment_v0_2_prompt_0_4.json')
        self.assertEqual({key for key in original if original[key]!=revised[key]},
                         {'prompt_version','shared_system_constraints'})
        audit=json.loads((ASSESSMENT/'prompt_revision.json').read_text())
        self.assertEqual(revised['shared_system_constraints'],original['shared_system_constraints']+'\n'+audit['appended_instruction'])
        self.assertEqual(r.sha((r.ROOT/'configs/experiment_v0_2.json').read_bytes()),audit['source_config_sha256'])
        self.assertEqual(revised['generation']['seeds'],[20261019,20261020,20261021])
        for field in ('model','generation','retrieval','rag_addition','rules_version','fallback'):
            self.assertEqual(original[field],revised[field])
        self.assertNotIn('S16',audit['appended_instruction'])
        self.assertNotIn('illustrative_question',audit['appended_instruction'])


if __name__=='__main__':
    unittest.main()
