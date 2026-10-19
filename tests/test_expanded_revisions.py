"""Source-bound revision checks; no human decisions, model or network calls."""
import copy
from pathlib import Path
import unittest
import research as r
from scripts import apply_expanded_review as revisions


class ExpandedRevisionTests(unittest.TestCase):
    def setUp(self):
        self.batch = r.ROOT / revisions.BATCH
        self.before = {key: revisions.strict_rows(self.batch / 'before/data/exploratory_v0_2' / filename)
                       for key, filename in [('scenarios', 'scenarios.jsonl'), ('questions', 'question_bank.jsonl'),
                                             ('notes', 'evaluation_notes.jsonl')]}
        self.before['decisions'] = revisions.strict_rows(self.batch / 'before/data/reviews/decisions.jsonl')
        self.proposals = revisions.strict_rows(self.batch / revisions.SOURCE_NAMES[1])
        self.markdown = (self.batch / revisions.SOURCE_NAMES[0]).read_text(encoding='utf-8')
        self.review = (self.batch / 'before/reports/exploratory_v0_2/review.md').read_bytes()

    def plan(self, data=None, proposals=None, markdown=None, review=None):
        return revisions.plan(data if data is not None else self.before,
                              proposals if proposals is not None else self.proposals,
                              markdown if markdown is not None else self.markdown,
                              review if review is not None else self.review)

    def test_exact_changes_preserve_all_other_fields_and_pending_status(self):
        before = copy.deepcopy(self.before)
        updated, applications = self.plan()
        self.assertEqual(self.before, before)
        self.assertEqual(len(applications), 11)
        self.assertEqual(sum(len(row['changes']) for row in applications), 12)
        self.assertEqual(updated['decisions'], [])
        self.assertTrue(all(row['review_status'] == 'pending_human_review'
                            for key in ('scenarios', 'questions', 'notes') for row in updated[key]))
        # Only S42/S52 input activities change; S55 and all injection notes stay exact.
        old = {row['scenario_id']: row for row in before['scenarios']}
        for row in updated['scenarios']:
            expected = copy.deepcopy(old[row['scenario_id']])
            if row['scenario_id'] in ('S42', 'S52'):
                expected['context']['planned_activity'] = row['context']['planned_activity']
            self.assertEqual(row, expected)
        check = revisions.verify_application(r.ROOT)
        self.assertEqual(check['applied_records'], 11)
        self.assertEqual(check['applied_fields'], 12)
        self.assertEqual(check['human_approval_effect'], 'none')

    def test_context_notes_and_question_version_mismatches_block(self):
        for key, field in [('scenarios', 'context'), ('notes', 'intended_reflection'),
                           ('questions', 'question_text')]:
            changed = copy.deepcopy(self.before)
            if field == 'context':
                changed[key][16][field]['planned_minutes'] += 1
            else:
                changed[key][0][field] += ' changed fixture'
            with self.assertRaisesRegex(ValueError, 'target_version_mismatch'):
                self.plan(data=changed)

    def test_readable_source_hash_and_replacements_must_agree(self):
        with self.assertRaisesRegex(ValueError, 'document_version_mismatch'):
            self.plan(review=self.review + b'changed fixture')
        bad = self.markdown.replace('How did you match the example values to their schema types?', 'Fixture mismatch?')
        with self.assertRaisesRegex(ValueError, 'markdown_jsonl_revision_mismatch'):
            self.plan(markdown=bad)
        changed = copy.deepcopy(self.proposals)
        row = next(row for row in changed if row['record_id'] == 'S17')
        row['proposed_changes'] = {'context.student_note': 'Forbidden scope change'}
        with self.assertRaisesRegex(ValueError, 'unsupported_revision_field'):
            self.plan(proposals=changed)

    def test_proposals_cannot_become_human_decisions_or_duplicate_targets(self):
        changed = copy.deepcopy(self.proposals)
        changed[0]['human_decision'] = 'accept'
        with self.assertRaisesRegex(ValueError, 'must_not_be_human_decisions'):
            self.plan(proposals=changed)
        with self.assertRaisesRegex(ValueError, 'targets_differ'):
            self.plan(proposals=self.proposals + self.proposals[:1])
        # The 79 accept proposals do not write a single human decision.
        updated, _ = self.plan()
        self.assertEqual(updated['decisions'], self.before['decisions'])


if __name__ == '__main__':
    unittest.main()
