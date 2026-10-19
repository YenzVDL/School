"""Apply the explicitly requested 11 assistant revisions; no human review or inference.

Default is a read-only preview. --apply preserves sources and pre-change files,
then records field/target hashes separately from the human decision log.
"""
import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import research as r

DATASET = 'exploratory_v0_2'
BATCH = Path('data/reviews/expanded_pilot_review_20261019')
SOURCE_NAMES = ('Expanded_Pilot_Review.md', 'Assistant_Review_Proposals.jsonl')
EXPECTED = {
    **{rid: {'evaluation_notes.illustrative_question_not_gold_label'}
       for rid in ('S17', 'S27', 'S30', 'S40', 'S50', 'S60')},
    **{rid: {'context.planned_activity'} for rid in ('S42', 'S52')},
    'S55': {'evaluation_notes.intended_reflection', 'evaluation_notes.illustrative_question_not_gold_label'},
    'Q24': {'question_text'}, 'Q26': {'question_text'},
}


def strict_rows(path):
    errors = []
    rows = r.load_rows(path, 'assistant_source', errors)
    if errors:
        raise ValueError('invalid_assistant_source_jsonl')
    return rows


def plan(data, proposals, markdown, source_review_bytes):
    """Pure planning: reject stale sources/unsupported changes before any writes."""
    reference = re.search(r'Review source SHA-256: `([0-9a-f]{64})`', markdown)
    if not reference or reference.group(1) != r.sha(source_review_bytes):
        raise ValueError('source_review_document_version_mismatch')
    targets = r.target_hashes(data)
    keys = [(row.get('record_type'), row.get('record_id')) for row in proposals]
    if len(keys) != len(set(keys)) or set(keys) != set(targets):
        raise ValueError('assistant_source_targets_differ')
    revisions = {}
    for row in proposals:
        key = (row['record_type'], row['record_id'])
        if row.get('source_target_sha256') != targets[key]:
            raise ValueError('assistant_source_target_version_mismatch')
        if (row.get('review_kind') != 'assistant_proposal' or row.get('human_decision') is not None
                or row.get('human_reviewer_code') is not None):
            raise ValueError('assistant_proposals_must_not_be_human_decisions')
        if row.get('proposed_decision') not in {'accept', 'revise', 'reject'}:
            raise ValueError('invalid_assistant_proposal')
        changes = row.get('proposed_changes')
        if not isinstance(changes, dict) or bool(changes) != (row['proposed_decision'] == 'revise'):
            raise ValueError('revision_changes_required_only_for_revise')
        if changes:
            revisions[row['record_id']] = row
    if set(revisions) != set(EXPECTED):
        raise ValueError('expected_eleven_revisions')
    # Check that the readable source and machine-readable changes actually agree.
    sections = dict(re.findall(r'^### ([SQ]\d+)\s*\n(.*?)(?=^### |^## |\Z)', markdown, re.M | re.S))
    updated = copy.deepcopy(data)
    scenarios = {row['scenario_id']: row for row in updated['scenarios']}
    notes = {row['scenario_id']: row for row in updated['notes']}
    questions = {row['question_id']: row for row in updated['questions']}
    applications = []
    for rid, row in revisions.items():
        changes = row['proposed_changes']
        if set(changes) != EXPECTED[rid]:
            raise ValueError('unsupported_revision_field')
        readable = dict(re.findall(r'\*\*([a-z_.]+)\*\*\s*\n\s*> ([^\n]+)', sections.get(rid, '')))
        if readable != changes:
            raise ValueError('markdown_jsonl_revision_mismatch')
        applied = {}
        for field, value in changes.items():
            if not r.nonempty(value):
                raise ValueError('nonempty_replacement_required')
            if field.startswith('evaluation_notes.'):
                record, name = notes[rid], field.split('.')[1]
            elif field.startswith('context.'):
                record, name = scenarios[rid]['context'], field.split('.')[1]
            else:
                record, name = questions[rid], field
            applied[field] = {'before': record[name], 'after': value}
            record[name] = value
        applications.append(dict(record_type=row['record_type'], record_id=rid,
                                 before_target_sha256=row['source_target_sha256'], changes=applied,
                                 reason=row['reason'], conditions=row['conditions'],
                                 source_kind='assistant_proposal', human_approval_effect='none'))
    after = r.target_hashes(updated)
    for row in applications:
        row['after_target_sha256'] = after[(row['record_type'], row['record_id'])]
    return updated, applications


def apply(root, source_dir, commit=False):
    previous = r.DATA.name
    try:
        r.configure_dataset(DATASET)
        report, data, _ = r.validate(root)
        r.require_valid(report)
        manifest_path = root / r.DATA / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for name, digest in manifest['file_sha256'].items():
            if r.sha((root / r.DATA / name).read_bytes()) != digest:
                raise ValueError('working_manifest_version_mismatch')
        for name, digest in manifest['preserved_source_sha256'].items():
            if r.sha((root / name).read_bytes()) != digest:
                raise ValueError('protected_history_version_mismatch')
        proposals = strict_rows(source_dir / SOURCE_NAMES[1])
        markdown = (source_dir / SOURCE_NAMES[0]).read_text(encoding='utf-8')
        updated, applications = plan(data, proposals, markdown, (root / r.REPORTS / 'review.md').read_bytes())
        result = dict(status='preview', source_targets_verified=len(proposals), source_document_verified=True,
                      proposed_decisions=dict(Counter(row['proposed_decision'] for row in proposals)),
                      revised_records=len(applications), revised_fields=sum(len(row['changes']) for row in applications),
                      human_approval_effect='none', inference_run=False)
        if not commit:
            return result
        batch = root / BATCH
        if batch.exists():
            raise ValueError('application_batch_already_exists_do_not_overwrite')
        # Validate the complete proposed files in a temporary local copy first.
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary)
            for path in (r.RAW, r.REVIEW, r.DATA):
                shutil.copytree(root / path, staging / path)
            for key in ('scenarios', 'questions', 'notes'):
                r.write_jsonl(staging / r.FILES[key], updated[key])
            candidate, _, _ = r.validate(staging)
            r.require_valid(candidate)
            if candidate['privacy_screening']['findings']:
                raise ValueError('privacy_findings_require_review')
        # Preserve exact sources and before-state, including the reviewed Markdown.
        protected = {path.relative_to(root).as_posix(): r.sha(path.read_bytes())
                     for folder in ('data/raw', 'data/pilot_v0_1', 'data/reviews')
                     for path in (root / folder).rglob('*') if path.is_file()}
        protected.update({name: r.sha((root / name).read_bytes()) for name in
                          ('approaches.py', 'ollama_local.py', 'configs/experiment_v0_2.json')})
        batch.mkdir(parents=True)
        for name in SOURCE_NAMES:
            shutil.copyfile(source_dir / name, batch / name)
        snapshots = {}
        for path in [*r.FILES.values(), r.DATA / 'manifest.json',
                     *[r.REPORTS / name for name in ('review.md', 'review_summary.md', 'review_forms.jsonl',
                                                    'assistant_review_proposals.jsonl')]]:
            destination = batch / 'before' / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
            snapshots[path.as_posix()] = r.sha(destination.read_bytes())
        source_hashes = {name: r.sha((batch / name).read_bytes()) for name in SOURCE_NAMES}
        applied_at = datetime.now(timezone.utc).isoformat()
        for row in applications:
            row.update(application_id='expanded-20261019-' + row['record_id'], applied_at_utc=applied_at,
                       source_proposals_sha256=source_hashes[SOURCE_NAMES[1]],
                       authorization='User request to apply eleven specified revisions; no human decisions imported.')
        r.write_jsonl(batch / 'applications.jsonl', applications)
        for key in ('scenarios', 'questions', 'notes'):
            r.write_jsonl(root / r.FILES[key], updated[key])
        manifest['file_sha256'] = {name: r.sha((root / r.DATA / name).read_bytes()) for name in manifest['file_sha256']}
        manifest.setdefault('revision_batches', []).append(BATCH.as_posix())
        r.write_json(manifest_path, manifest)
        result.update(status='applied', applied_at_utc=applied_at, source_sha256=source_hashes,
                      before_sha256=snapshots, protected_sha256=protected,
                      after_file_sha256=manifest['file_sha256'],
                      note='S55 category retained as challenge bucket; excess count is ambiguous extra work, not proven contradiction.')
        r.write_json(batch / 'application_manifest.json', result)
        return result
    finally:
        r.configure_dataset(previous)


def verify_application(root):
    """Verify exact changes and preserved bytes, without modifying data or calling models."""
    batch = root / BATCH
    manifest = json.loads((batch / 'application_manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['source_sha256'].items():
        if r.sha((batch / name).read_bytes()) != digest:
            raise ValueError('assistant_source_snapshot_changed')
    for name, digest in manifest['before_sha256'].items():
        if r.sha((batch / 'before' / name).read_bytes()) != digest:
            raise ValueError('before_snapshot_changed')
    for name, digest in manifest['protected_sha256'].items():
        if name == 'data/reviews/decisions.jsonl':
            # Later authorized human reviews append; the original prefix stays exact.
            original = (batch / 'before' / name).read_bytes()
            if not (root / name).read_bytes().startswith(original) or r.sha(original) != digest:
                raise ValueError('original_review_history_prefix_changed')
            continue
        if r.sha((root / name).read_bytes()) != digest:
            raise ValueError('protected_history_or_inference_configuration_changed')
    paths = {'scenarios': 'scenarios.jsonl', 'questions': 'question_bank.jsonl', 'notes': 'evaluation_notes.jsonl'}
    before = {key: strict_rows(batch / 'before/data' / DATASET / name) for key, name in paths.items()}
    expected, planned = plan(before, strict_rows(batch / SOURCE_NAMES[1]),
                             (batch / SOURCE_NAMES[0]).read_text(encoding='utf-8'),
                             (batch / 'before/reports' / DATASET / 'review.md').read_bytes())
    actual = {key: strict_rows(root / 'data' / DATASET / name) for key, name in paths.items()}
    if expected != actual:
        raise ValueError('working_data_differs_from_exact_revisions')
    applications = strict_rows(batch / 'applications.jsonl')
    if len(applications) != len(planned):
        raise ValueError('application_history_count_differs')
    for saved, intended in zip(applications, planned):
        if any(saved.get(key) != value for key, value in intended.items()):
            raise ValueError('application_history_differs')
    for name, digest in manifest['after_file_sha256'].items():
        if r.sha((root / 'data' / DATASET / name).read_bytes()) != digest:
            raise ValueError('applied_file_hash_differs')
    return dict(source_targets_verified=manifest['source_targets_verified'], source_document_verified=True,
                applied_records=len(applications), applied_fields=sum(len(row['changes']) for row in applications),
                exact_revisions_verified=True, protected_files_verified=len(manifest['protected_sha256']),
                raw_and_review_history_preserved=True, human_approval_effect='none', inference_run=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Apply the user-authorized revisions after source checks')
    args = parser.parse_args()
    result = apply(r.ROOT, args.source_directory, args.apply)
    print(json.dumps({key: result[key] for key in ('status', 'source_targets_verified', 'source_document_verified',
                     'revised_records', 'revised_fields', 'human_approval_effect', 'inference_run')}, indent=2))


if __name__ == '__main__':
    main()
