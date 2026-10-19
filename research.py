"""Local data preparation for subtask 5. No inference or network operations."""
import argparse
from collections import Counter, defaultdict
from datetime import date
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import types
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent
RAW = Path('data/raw/reflection_pilot_v0_1')
PACKAGE = RAW / 'package/reflection_pilot_v0_1'
ARCHIVE = RAW / 'Reflection_Question_Pilot_v0_1.zip'
ARCHIVE_SHA256 = '08a7cba88af8314dc62bf214826cd3161cd950703b78a8a7b54766e4b1f1549d'
DATA = Path('data/pilot_v0_1')
REPORTS = Path('reports')
EXPORTS = Path('exports')
SPLITS = {'development', 'validation', 'test'}
REVIEW = Path('data/reviews')
FILES = {'scenarios': DATA / 'scenarios.jsonl',
         'questions': DATA / 'question_bank.jsonl',
         'notes': DATA / 'evaluation_notes.jsonl',
         'requests': REVIEW / 'requests.jsonl',
         'decisions': REVIEW / 'decisions.jsonl'}
REVIEW_EVIDENCE = {'review_proposals': REVIEW / 'proposals.jsonl',
                   'revision_proposals': REVIEW / 'revision_proposals.jsonl'}
CONTEXT = ('learning_goal', 'planned_activity', 'planned_minutes',
           'reported_completed_units', 'planned_units', 'reported_minutes',
           'progress_status', 'student_note', 'previous_question')
QUESTION_EXPORT = ('question_id', 'reflection_focus', 'question_text',
                   'applicable_when', 'avoid_when')
CRITERIA = ('realism', 'clarity', 'relevance', 'unsupported_assumptions',
            'autonomy', 'sensitive_information')
PROGRESS = {'completed', 'partially_completed', 'not_started', 'unknown', 'rescheduled'}
CATEGORIES = {'completed_as_planned', 'partially_completed', 'more_time_than_planned',
              'missing_progress', 'contradictory_progress', 'rescheduled_by_student',
              'less_time_than_planned', 'self_reported_difficulty',
              'avoid_repeated_question', 'instruction_in_student_note'}
FOCI = {'learning_outcome', 'learning_strategy', 'time_use', 'progress_clarification',
        'record_clarification', 'planning_fit', 'checking_understanding',
        'reported_difficulty', 'open_uncertainty', 'optional_next_attempt'}
PATTERNS = {'email_like': r'\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b',
            'phone_like': r'(?<!\w)\+\d[\d ()-]{7,}\d', 'url_like': r'https?://\S+'}


def configure_dataset(name):
    """CLI selection; imported library functions retain the original pilot defaults."""
    global DATA, FILES, REPORTS, EXPORTS
    if name not in {'pilot_v0_1', 'exploratory_v0_2'}:
        raise ValueError('unknown_dataset')
    DATA = Path('data') / name
    REPORTS = Path('reports') if name == 'pilot_v0_1' else Path('reports') / name
    EXPORTS = Path('exports') if name == 'pilot_v0_1' else Path('exports') / name
    FILES = {'scenarios': DATA / 'scenarios.jsonl', 'questions': DATA / 'question_bank.jsonl',
             'notes': DATA / 'evaluation_notes.jsonl',
             'requests': REVIEW / 'requests.jsonl' if name == 'pilot_v0_1' else DATA / 'review_requests.jsonl',
             'decisions': REVIEW / 'decisions.jsonl'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(packed(row) + '\n' for row in rows), encoding='utf-8')


def verify_raw(root):
    """Trust the pinned archive; check every extracted byte without executing it."""
    archive = root / ARCHIVE
    if not archive.is_file() or sha(archive.read_bytes()) != ARCHIVE_SHA256:
        raise ValueError('raw_archive_integrity_failed')
    hashes = {}
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            if entry.is_dir():
                continue
            path = root / RAW / 'package' / entry.filename
            expected = sha(source.read(entry))
            if not path.is_file() or sha(path.read_bytes()) != expected:
                raise ValueError('raw_extracted_integrity_failed')
            hashes[entry.filename] = expected
    extracted_files = {path.relative_to(root / RAW / 'package').as_posix()
                       for path in (root / RAW / 'package').rglob('*') if path.is_file()}
    if extracted_files != set(hashes):
        raise ValueError('raw_snapshot_has_extra_files')
    return {'snapshot_version': 'reflection_pilot_v0_1',
            'archive_sha256': ARCHIVE_SHA256, 'files_sha256': hashes}


def initialize(root):
    manifest = verify_raw(root)
    manifest_path = root / RAW / 'manifest.json'
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding='utf-8')) != manifest:
            raise ValueError('raw_manifest_integrity_failed')
    else:
        write_json(manifest_path, manifest)
    # Preserve the later separately supplied files under their original upload names.
    supplied = root / 'data/raw/supplied_files'
    if supplied.is_dir():
        mapping = []
        for path in sorted(supplied.iterdir()):
            if not path.is_file() or path.name == 'mapping.jsonl':
                continue
            digest = sha(path.read_bytes())
            matches = [name for name, value in manifest['files_sha256'].items() if value == digest]
            if len(matches) != 1:
                raise ValueError('supplied_file_does_not_match_archive')
            mapping.append({'supplied_filename': path.name, 'sha256': digest,
                            'matching_archive_entry': matches[0]})
        mapping_path = supplied / 'mapping.jsonl'
        if not mapping_path.exists():
            write_jsonl(mapping_path, mapping)
        elif mapping_path.read_text(encoding='utf-8') != ''.join(packed(row) + '\n' for row in mapping):
            raise ValueError('supplied_file_mapping_integrity_failed')
    if DATA.name != 'pilot_v0_1':
        if not all((root / path).is_file() for path in FILES.values()):
            raise ValueError('versioned_working_dataset_missing_restore_from_local_versioned_files')
        return
    copies = {FILES['scenarios']: 'scenarios.jsonl', FILES['questions']: 'question_bank.jsonl',
              FILES['notes']: 'evaluation_notes.jsonl', FILES['requests']: 'human_review_log.jsonl'}
    for destination, source in copies.items():
        target = root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        # Existing working records and completed reviews are never reconstructed.
        if not target.exists():
            shutil.copyfile(root / PACKAGE / source, target)
    decisions = root / FILES['decisions']
    if not decisions.exists():
        decisions.write_text('', encoding='utf-8')


def issue(errors, file, row, code, field=None):
    # Never echo supplied IDs, values, keys, matched text or exception messages.
    item = {'file': file, 'row': row, 'code': code}
    if field is not None:
        item['field'] = field
    errors.append(item)


def no_repeated_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite_number')


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('nonfinite_number')
    return number


def load_rows(path, name, errors):
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeError):
        issue(errors, name, None, 'unreadable_file')
        return []
    rows = []
    for line_no, line in enumerate(lines, 1):
        try:
            row = json.loads(line, object_pairs_hook=no_repeated_keys,
                             parse_constant=reject_constant, parse_float=finite_float)
            if not isinstance(row, dict):
                raise ValueError('object_required')
        except (ValueError, RecursionError):
            issue(errors, name, line_no, 'invalid_json_object')
            row = {}  # Retain line positions; invalid records cannot be exported.
        rows.append(row)
    return rows


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def member(value, allowed):
    return isinstance(value, str) and value in allowed


def shape(row, expected, name, line, errors):
    if set(row) != set(expected):
        issue(errors, name, line, 'missing_or_unknown_fields')


def text(row, fields, name, line, errors):
    for field in fields:
        if not nonempty(row.get(field)):
            issue(errors, name, line, 'nonempty_string_required', field)


def valid_id(value, prefix):
    return isinstance(value, str) and re.fullmatch(prefix + r'[0-9]{2,}', value) is not None


def validate_decision(row, name, line, errors, targets, form=False):
    fields = {'record_type', 'record_id', 'target_sha256', 'reviewer_code',
              'review_date', 'criteria', 'decision', 'reason'}
    if not form:
        fields.add('review_id')
    shape(row, fields, name, line, errors)
    kind, rid = row.get('record_type'), row.get('record_id')
    key = (kind, rid) if isinstance(kind, str) and isinstance(rid, str) else None
    if key not in targets:
        issue(errors, name, line, 'unknown_review_target')
    digest = row.get('target_sha256')
    if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
        issue(errors, name, line, 'invalid_target_hash')
    elif form and key in targets and digest != targets[key]:
        issue(errors, name, line, 'stale_review_form')
    code = row.get('reviewer_code')
    if not isinstance(code, str) or re.fullmatch(r'[A-Z0-9_-]{2,24}', code) is None:
        issue(errors, name, line, 'invalid_reviewer_code')
    value = row.get('review_date')
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except ValueError:
        issue(errors, name, line, 'invalid_review_date')
    if not member(row.get('decision'), {'accept', 'revise', 'reject'}):
        issue(errors, name, line, 'invalid_decision')
    text(row, ['reason'], name, line, errors)
    criteria = row.get('criteria')
    if not isinstance(criteria, dict):
        issue(errors, name, line, 'criteria_object_required')
    else:
        shape(criteria, CRITERIA, name, line, errors)
        for criterion in CRITERIA:
            if not member(criteria.get(criterion), {'pass', 'concern'}):
                issue(errors, name, line, 'invalid_criterion', criterion)
        if row.get('decision') == 'accept' and any(criteria.get(c) != 'pass' for c in CRITERIA):
            issue(errors, name, line, 'accept_requires_all_criteria_pass')
    if not form:
        try:
            if str(uuid.UUID(row.get('review_id'))) != row.get('review_id'):
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            issue(errors, name, line, 'invalid_review_id')


def target_hashes(data):
    notes = {r['scenario_id']: r for r in data['notes']}
    targets = {('scenario', r['scenario_id']): sha(packed({'record': r,
               'evaluation_notes': notes[r['scenario_id']]}).encode('utf-8')) for r in data['scenarios']}
    targets.update({('question', r['question_id']): sha(packed(r).encode('utf-8')) for r in data['questions']})
    return targets


def review_evidence(root, errors, targets=None):
    """Incomplete user proposals are evidence, never completed decisions."""
    evidence = {name: load_rows(root / path, name, errors) if (root / path).exists() else []
                for name, path in REVIEW_EVIDENCE.items()}
    proposals = {}
    for line, row in enumerate(evidence['review_proposals'], 1):
        name = 'review_proposals'
        shape(row, {'proposal_id', 'record_type', 'record_id', 'target_sha256', 'reviewer_code',
                    'review_date', 'criteria', 'proposed_decision', 'reason', 'condition', 'status'},
              name, line, errors)
        text(row, ['proposal_id', 'reason'], name, line, errors)
        pid = row.get('proposal_id')
        if isinstance(pid, str):
            if pid in proposals:
                issue(errors, name, line, 'duplicate_proposal_id')
            proposals[pid] = row
        kind = row.get('record_type')
        if not member(kind, {'scenario', 'question'}) or not valid_id(row.get('record_id'),
                'S' if kind == 'scenario' else 'Q'):
            issue(errors, name, line, 'invalid_review_target')
        elif targets is not None and (kind, row['record_id']) not in targets:
            issue(errors, name, line, 'unknown_review_target')
        digest = row.get('target_sha256')
        if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            issue(errors, name, line, 'invalid_target_hash')
        if row.get('reviewer_code') is not None or row.get('criteria') != dict.fromkeys(CRITERIA):
            issue(errors, name, line, 'proposal_is_unconfirmed_use_completed_form')
        try:
            value = row.get('review_date')
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except ValueError:
            issue(errors, name, line, 'invalid_review_date')
        if not member(row.get('proposed_decision'), {'accept', 'revise', 'reject'}):
            issue(errors, name, line, 'invalid_proposed_decision')
        if row.get('status') != 'proposal_only':
            issue(errors, name, line, 'invalid_proposal_status')
        if row.get('condition') is not None and not nonempty(row['condition']):
            issue(errors, name, line, 'nullable_string_required', 'condition')
    seen = set()
    for line, row in enumerate(evidence['revision_proposals'], 1):
        name = 'revision_proposals'
        shape(row, {'proposal_id', 'target_sha256', 'changes', 'status', 'implementation_note'},
              name, line, errors)
        pid = row.get('proposal_id')
        source = proposals.get(pid) if isinstance(pid, str) else None
        if source is None or source.get('proposed_decision') != 'revise':
            issue(errors, name, line, 'revision_requires_revise_proposal')
        elif source.get('target_sha256') != row.get('target_sha256'):
            issue(errors, name, line, 'revision_hash_differs_from_proposal')
        if isinstance(pid, str):
            if pid in seen:
                issue(errors, name, line, 'duplicate_revision_proposal')
            seen.add(pid)
        if row.get('status') != 'draft_for_re_review':
            issue(errors, name, line, 'invalid_revision_status')
        text(row, ['implementation_note'], name, line, errors)
        changes = row.get('changes')
        allowed = {'context.planned_activity', 'context.student_note', 'evaluation_notes.intended_reflection',
                   'evaluation_notes.illustrative_question_not_gold_label', 'question_text'}
        if not isinstance(changes, dict) or not changes or not set(changes).issubset(allowed):
            issue(errors, name, line, 'invalid_proposed_changes')
        else:
            for change in changes.values():
                if not isinstance(change, dict):
                    issue(errors, name, line, 'change_object_required')
                    continue
                shape(change, {'before', 'proposed'}, name, line, errors)
                text(change, ['before', 'proposed'], name, line, errors)
    return evidence


def approval_states(targets, decisions):
    """Latest append per reviewer wins; every participating reviewer must accept current bytes."""
    latest = defaultdict(dict)
    for row in decisions:
        latest[(row['record_type'], row['record_id'])][row['reviewer_code']] = row
    states = {}
    for key, digest in targets.items():
        reviews = list(latest[key].values())
        if not reviews:
            states[key] = 'pending'
        elif any(r['target_sha256'] != digest for r in reviews):
            states[key] = 'stale'
        elif any(r['decision'] == 'reject' for r in reviews):
            states[key] = 'reject'
        elif any(r['decision'] == 'revise' for r in reviews):
            states[key] = 'revise'
        else:
            states[key] = 'accepted'
    return states


def near_duplicate_flags(scenarios):
    """Inspectable wording heuristic, not a semantic duplicate detector."""
    texts = [' '.join(re.findall(r'[a-z0-9]+', row['context']['learning_goal'].casefold() + ' ' +
                  row['context']['planned_activity'].casefold())) for row in scenarios]
    flags = []
    for index, left in enumerate(texts):
        a = set(left.split())
        for other in range(index):
            right = texts[other]
            b = set(right.split())
            jaccard = len(a & b) / len(a | b) if a | b else 0
            ratio = SequenceMatcher(None, left, right, autojunk=False).ratio()
            if jaccard >= 0.72 or ratio >= 0.88:
                flags.append({'file': 'scenarios', 'row': index + 1, 'other_row': other + 1,
                              'code': 'possible_near_duplicate_review',
                              'same_family': scenarios[index]['scenario_family_id'] == scenarios[other]['scenario_family_id'],
                              'same_split': scenarios[index]['split'] == scenarios[other]['split'],
                              'token_jaccard': round(jaccard, 3), 'sequence_ratio': round(ratio, 3)})
    return flags


def validate(root):
    errors, flags, findings = [], [], []
    try:
        raw_manifest = verify_raw(root)
        saved = json.loads((root / RAW / 'manifest.json').read_text(encoding='utf-8'))
        if saved != raw_manifest:
            raise ValueError()
    except (OSError, ValueError, zipfile.BadZipFile):
        issue(errors, 'raw', None, 'raw_integrity_failed')
    data = {name: load_rows(root / path, name, errors) for name, path in FILES.items()}
    for name in ('scenarios', 'questions', 'notes', 'requests'):
        if not data[name]:
            issue(errors, name, None, 'empty_dataset')
    id_keys = {'scenarios': 'scenario_id', 'questions': 'question_id', 'notes': 'scenario_id',
               'decisions': 'review_id'}
    for name, key in id_keys.items():
        ids, records = set(), set()
        for line, row in enumerate(data[name], 1):
            value = row.get(key)
            if not isinstance(value, str) or value in ids:
                issue(errors, name, line, 'missing_or_duplicate_id', key)
            if isinstance(value, str):
                ids.add(value)
            fingerprint = packed(row)
            if fingerprint in records:
                issue(errors, name, line, 'duplicate_record')
            records.add(fingerprint)
    contexts, families = set(), defaultdict(set)
    scenario_ids, question_ids, note_ids = set(), set(), set()
    for line, row in enumerate(data['scenarios'], 1):
        name = 'scenarios'
        shape(row, {'scenario_id', 'scenario_family_id', 'category', 'split', 'synthetic',
                    'review_status', 'context'}, name, line, errors)
        for field, prefix in [('scenario_id', 'S'), ('scenario_family_id', 'F')]:
            if not valid_id(row.get(field), prefix):
                issue(errors, name, line, 'invalid_id', field)
        if isinstance(row.get('scenario_id'), str):
            scenario_ids.add(row['scenario_id'])
        if not member(row.get('category'), CATEGORIES):
            issue(errors, name, line, 'invalid_category')
        if not member(row.get('split'), SPLITS):
            issue(errors, name, line, 'invalid_split')
        elif isinstance(row.get('scenario_family_id'), str):
            families[row['scenario_family_id']].add(row['split'])
        if row.get('synthetic') is not True or row.get('review_status') != 'pending_human_review':
            issue(errors, name, line, 'invalid_provenance_or_status')
        context = row.get('context')
        if not isinstance(context, dict):
            issue(errors, name, line, 'context_object_required')
            continue
        shape(context, CONTEXT, name, line, errors)
        text(context, ['learning_goal', 'planned_activity'], name, line, errors)
        for field in ('student_note', 'previous_question'):
            if context.get(field) is not None and not isinstance(context[field], str):
                issue(errors, name, line, 'nullable_string_required', field)
        for field in ('planned_minutes', 'reported_completed_units', 'planned_units', 'reported_minutes'):
            value = context.get(field)
            if value is not None and (type(value) is not int or value < 0):
                issue(errors, name, line, 'nullable_nonnegative_integer_required', field)
        if not member(context.get('progress_status'), PROGRESS):
            issue(errors, name, line, 'invalid_progress_status')
        fingerprint = packed(context)
        if fingerprint in contexts:
            issue(errors, name, line, 'duplicate_context')
        contexts.add(fingerprint)
        for field in CONTEXT:
            if field in context and context[field] is None:
                flags.append({'file': name, 'row': line, 'code': 'missing_context_preserved', 'field': field})
        if context.get('progress_status') == 'unknown':
            flags.append({'file': name, 'row': line, 'code': 'missing_progress_preserved'})
        count, total = context.get('reported_completed_units'), context.get('planned_units')
        if type(count) is int and type(total) is int:
            if count > total:
                flags.append({'file': name, 'row': line, 'code': 'count_exceeds_plan_preserved'})
            if context.get('progress_status') == 'completed' and count < total:
                flags.append({'file': name, 'row': line, 'code': 'contradictory_progress_preserved'})
    for splits in families.values():
        if len(splits) > 1:
            issue(errors, 'scenarios', None, 'scenario_family_overlap')
    qtexts = set()
    for line, row in enumerate(data['questions'], 1):
        shape(row, {'question_id', 'reflection_focus', 'question_text', 'applicable_when',
                    'avoid_when', 'provenance', 'review_status'}, 'questions', line, errors)
        if not valid_id(row.get('question_id'), 'Q'):
            issue(errors, 'questions', line, 'invalid_id')
        if isinstance(row.get('question_id'), str):
            question_ids.add(row['question_id'])
        text(row, ['question_text', 'applicable_when', 'avoid_when', 'provenance'], 'questions', line, errors)
        if not member(row.get('reflection_focus'), FOCI):
            issue(errors, 'questions', line, 'invalid_reflection_focus')
        if row.get('review_status') != 'pending_human_review':
            issue(errors, 'questions', line, 'invalid_review_status')
        if isinstance(row.get('question_text'), str):
            normalized = ' '.join(row['question_text'].casefold().split())
            if normalized in qtexts:
                issue(errors, 'questions', line, 'duplicate_question_text')
            qtexts.add(normalized)
    for line, row in enumerate(data['notes'], 1):
        shape(row, {'scenario_id', 'intended_reflection', 'unsupported_assumptions_to_avoid',
                    'illustrative_question_not_gold_label', 'intentional_input_challenge',
                    'review_status'}, 'notes', line, errors)
        if not valid_id(row.get('scenario_id'), 'S'):
            issue(errors, 'notes', line, 'invalid_id')
        if isinstance(row.get('scenario_id'), str):
            note_ids.add(row['scenario_id'])
        text(row, ['intended_reflection', 'illustrative_question_not_gold_label'], 'notes', line, errors)
        assumptions = row.get('unsupported_assumptions_to_avoid')
        if not isinstance(assumptions, list) or not assumptions or not all(nonempty(v) for v in assumptions):
            issue(errors, 'notes', line, 'nonempty_string_list_required')
        if type(row.get('intentional_input_challenge')) is not bool:
            issue(errors, 'notes', line, 'boolean_required')
        if row.get('review_status') != 'pending_human_review':
            issue(errors, 'notes', line, 'invalid_review_status')
    if scenario_ids != note_ids:
        issue(errors, 'notes', None, 'scenario_note_ids_differ')
    request_targets = set()
    for line, row in enumerate(data['requests'], 1):
        shape(row, {'record_type', 'record_id', 'reviewer_code', 'review_date',
                    'realism_or_applicability', 'autonomy_and_assumptions',
                    'privacy_and_sensitive_content', 'decision', 'notes'}, 'requests', line, errors)
        kind, rid = row.get('record_type'), row.get('record_id')
        if not member(kind, {'scenario', 'question'}) or not isinstance(rid, str):
            issue(errors, 'requests', line, 'invalid_review_target')
            continue
        key = (kind, rid)
        if key in request_targets:
            issue(errors, 'requests', line, 'duplicate_review_target')
        request_targets.add(key)
        if row.get('decision') != 'pending' or any(row.get(k) is not None for k in
                ('reviewer_code', 'review_date', 'realism_or_applicability', 'autonomy_and_assumptions',
                 'privacy_and_sensitive_content', 'notes')):
            issue(errors, 'requests', line, 'request_must_remain_blank_use_decisions')
    expected_targets = {('scenario', rid) for rid in scenario_ids} | {('question', rid) for rid in question_ids}
    if request_targets != expected_targets:
        issue(errors, 'requests', None, 'review_targets_differ')
    targets = target_hashes(data) if not errors else {}
    # The append-only decision log is shared by versioned datasets. Historical
    # decisions for IDs in another local version remain valid history; only
    # this version's exact current hashes determine its effective acceptance.
    history_targets = dict(targets)
    for version in ('pilot_v0_1', 'exploratory_v0_2'):
        if version == DATA.name:
            continue
        for kind, filename, id_key, prefix in [('scenario','scenarios.jsonl','scenario_id','S'),
                                               ('question','question_bank.jsonl','question_id','Q')]:
            path = root / 'data' / version / filename
            if path.is_file():
                for row in load_rows(path, 'historical_version', []):
                    if valid_id(row.get(id_key), prefix):
                        history_targets.setdefault((kind,row[id_key]), None)
    for line, row in enumerate(data['decisions'], 1):
        validate_decision(row, 'decisions', line, errors, history_targets)
    evidence = review_evidence(root, errors, targets)
    # Reuse original structural rules without its unsafe main() export side effect.
    supplied_status = 'not_run_invalid_structure'
    if not errors:
        # Execute the verified source as a module without creating raw __pycache__ files.
        source = root / PACKAGE / 'validate.py'
        module = types.ModuleType('supplied_validator')
        module.__file__ = str(source)
        exec(compile(source.read_bytes(), str(source), 'exec'), module.__dict__)
        # Original validator has only development/test. Adapt a copy for that legacy rule;
        # the unmodified three-way family/split checks above remain authoritative.
        legacy_scenarios = [dict(row, split='test' if row['split'] == 'validation' else row['split'])
                            for row in data['scenarios']]
        supplied_errors, _ = module.check(legacy_scenarios, data['questions'], data['notes'])
        for _ in supplied_errors:
            issue(errors, 'supplied_validator', None, 'supplied_check_failed')
        supplied_status = 'passed' if not supplied_errors else 'failed'
        flags.extend(near_duplicate_flags(data['scenarios']))
    # Screen every canonical file, including reviewer free text, without matched content.
    for name, rows in (data | evidence).items():
        for line, row in enumerate(rows, 1):
            content = packed(row)
            for kind, pattern in PATTERNS.items():
                if re.search(pattern, content):
                    findings.append({'file': name, 'row': line, 'kind': kind})
    states = approval_states(targets, data['decisions']) if not errors else {}
    hashes = {str(path).replace('\\', '/'): sha((root / path).read_bytes())
              for path in FILES.values() if (root / path).is_file()}
    report = {'report_version': '2', 'dataset_version': DATA.name,
              'structural_validation': {'status': 'failed' if errors else 'passed',
                                        'errors': errors, 'supplied_validator': supplied_status,
                                        'legacy_split_adapter': 'Validation mapped to test in a copy only; full three-way checks run independently.'},
              'data_quality_flags': flags,
              'privacy_screening': {'regex_status': 'findings_require_review' if findings else 'no_pattern_matches',
                                    'findings': findings, 'presidio': 'not_run',
                                    'limitation': 'Narrow contact patterns only; no anonymity or safety guarantee.'},
              'human_approval': {'counts': dict(Counter(states.values())),
                                 'policy': 'Every latest reviewer decision must accept the current target hash.'},
              'review_proposals': {'counts': dict(Counter(row.get('proposed_decision')
                                      for row in evidence['review_proposals']
                                      if isinstance(row.get('proposed_decision'), str))),
                                   'revision_drafts': len(evidence['revision_proposals']),
                                   'approval_effect': 'none; proposals are not completed decisions'},
              'counts': {name: len(rows) for name, rows in data.items()},
              'splits': dict(Counter(r['split'] for r in data['scenarios'] if member(r.get('split'), SPLITS))),
              'categories_by_split': {split: dict(sorted(Counter(row.get('category') for row in data['scenarios']
                                         if row.get('split') == split and isinstance(row.get('category'), str)).items()))
                                      for split in sorted(SPLITS)},
              'input_sha256': hashes, 'raw_archive_sha256': ARCHIVE_SHA256,
              'review_evidence_sha256': {str(path).replace('\\', '/'): sha((root / path).read_bytes())
                                        for path in REVIEW_EVIDENCE.values() if (root / path).is_file()},
              'workflow_sha256': sha(Path(__file__).read_bytes()),
              'python_version': sys.version.split()[0],
              'limitations': ['Synthetic draft; pending independent human review.',
                              'Splits are provisional; not a validated benchmark or independently held-out evidence.',
                              'No model results, compliance or pedagogical certification.']}
    return report, data, states


def require_valid(report):
    if report['structural_validation']['status'] != 'passed':
        raise ValueError('structural_validation_failed_see_report')


def render_review(root):
    report, data, states = validate(root)
    write_json(root / REPORTS / 'validation_report.json', report)
    require_valid(report)
    targets = target_hashes(data)
    sections = ['# Pilot human review', '',
                'Generated from JSONL; do not edit this document. Local reviewer material only.',
                'Synthetic draft. Provisional splits. Not a validated benchmark.',
                'Evaluation notes and illustrations must never be model inputs or retrieval content.', '',
                'Review each criterion: realism, clarity, relevance, unsupported assumptions, autonomy,',
                'and sensitive information. Use pass or concern. Accept requires six pass ratings.',
                'Record explicit accept/revise/reject, reviewer code, ISO date and reasons in a copied JSONL form.',
                'Check plausibility, English wording, fit to context, invented facts, pressure/disclosure,',
                'and identifying or unnecessary sensitive information. Do not answer the reflection question.',
                'Preserve deliberate nulls, zeros and contradictions; inspect challenges S04, S05 and S10.',
                'Second reviewers should rate independently; discuss differences and append revised decisions.',
                'No review is completed by generating this file. See README for submission commands.', '']
    notes = {row['scenario_id']: row for row in data['notes']}
    forms = []
    for kind, rows, id_key in [('scenario', data['scenarios'], 'scenario_id'),
                                ('question', data['questions'], 'question_id')]:
        for row in rows:
            key = (kind, row[id_key])
            sections += [f'## {kind} {row[id_key]}', '', f'Current decision: {states[key]}', '',
                         '```json', json.dumps(row, indent=2, ensure_ascii=False), '```', '']
            if kind == 'scenario':
                sections += ['Evaluation only:', '', '```json',
                             json.dumps(notes[row[id_key]], indent=2, ensure_ascii=False), '```', '']
            sections += ['Review form fields: ' + ', '.join(CRITERIA) + '.',
                         'Decision: accept / revise / reject. Reviewer code: __. Date: YYYY-MM-DD. Reason: __.', '']
            forms.append({'record_type': kind, 'record_id': row[id_key], 'target_sha256': targets[key],
                          'reviewer_code': None, 'review_date': None,
                          'criteria': dict.fromkeys(CRITERIA), 'decision': 'pending', 'reason': None})
    sections += ['## Recorded review history', '', '```json',
                 json.dumps(data['decisions'], indent=2, ensure_ascii=False), '```', '']
    evidence = review_evidence(root, [])
    if evidence['review_proposals']:
        def cell(value):
            return str(value).replace('|', '\\|').replace('\r', '').replace('\n', '<br>')

        sections += ['## Human review proposals and revision drafts', '',
                     'These proposals have no approval effect. Reviewer code and criterion ratings are unconfirmed.',
                     'Draft definitions are retained as history; application status is derived from current JSONL.',
                     'Applying a revision does not approve a record. All changed records require human re-review.',
                     'Pilot clarification questions may be considered for missing/conflicting context;',
                     'team integration and availability of previous_question remain unconfirmed.', '',
                     '| Record | Proposal | Review date | Condition | Original reason |',
                     '|---|---|---|---|---|']
        proposals = {row['proposal_id']: row for row in evidence['review_proposals']}
        for row in evidence['review_proposals']:
            sections.append('| ' + ' | '.join(cell(value) for value in
                (row['record_id'], row['proposed_decision'], row['review_date'],
                 row['condition'] or '', row['reason'])) + ' |')
        sections += ['', '### Revision changes and current application status', '']
        for revision in evidence['revision_proposals']:
            proposal = proposals[revision['proposal_id']]
            current = next(row for row in data['scenarios' if proposal['record_type'] == 'scenario' else 'questions']
                           if row.get('scenario_id', row.get('question_id')) == proposal['record_id'])
            matches = []
            for field, change in revision['changes'].items():
                if field.startswith('evaluation_notes.'):
                    value = notes[proposal['record_id']][field.split('.', 1)[1]]
                elif field.startswith('context.'):
                    value = current['context'][field.split('.', 1)[1]]
                else:
                    value = current.get(field)
                matches.append(value == change['proposed'])
            status = ('Applied to working data; pending human re-review.' if all(matches) else
                      'Partially applied or subsequently changed; compare current data.' if any(matches) else
                      'Not applied to current working data.')
            sections += [f"#### {proposal['record_id']}", '',
                         'Application status: **' + status + '**', '',
                         'Original reviewed SHA-256: `' + revision['target_sha256'] + '`.', '',
                         'Current target SHA-256: `' + targets[(proposal['record_type'], proposal['record_id'])] + '`.', '',
                         '| Field | Before | Draft replacement |', '|---|---|---|']
            for field, change in revision['changes'].items():
                sections.append('| ' + ' | '.join(cell(value) for value in
                    (field, change['before'], change['proposed'])) + ' |')
            sections += ['', revision['implementation_note'], '']
    sections += expanded_revision_sections(root, targets, states)
    (root / REPORTS).mkdir(parents=True, exist_ok=True)
    (root / REPORTS / 'review.md').write_text('\n'.join(sections), encoding='utf-8')
    write_jsonl(root / REPORTS / 'review_forms.jsonl', forms)
    render_summary(root, data, report)


def expanded_revision_sections(root, targets, states):
    """Render the separate assistant application log; it never supplies approval states."""
    batch = root / REVIEW / 'expanded_pilot_review_20261019'
    path = batch / 'applications.jsonl'
    if DATA.name != 'exploratory_v0_2' or not path.is_file():
        return []
    errors = []
    rows = load_rows(path, 'assistant_applications', errors)
    if errors:
        raise ValueError('invalid_assistant_application_log')
    lines = ['## Applied assistant revision proposals', '',
             'Separate assistant evidence: data/reviews/expanded_pilot_review_20261019/.',
             'The supplied 79 accept / 11 revise proposals are not human decisions or criterion scores.',
             'Eleven revisions were applied. Their application itself has no approval effect; current decisions come from the human log.',
             'Original source proposals refer to pre-revision target hashes, not approval of revised content.',
             'S55 retains its category as a challenge bucket; its excess count may reflect extra work.',
             'Pilot clarification and previous_question interface assumptions remain unconfirmed.', '',
             '| Record | Changed fields | Current version matches application |', '|---|---|---|']
    for row in rows:
        matches = targets.get((row['record_type'], row['record_id'])) == row['after_target_sha256']
        lines.append('| ' + ' | '.join((row['record_id'], ', '.join(row['changes']),
                                      'yes; ' + states.get((row['record_type'], row['record_id']), 'pending')
                                      if matches else 'no; inspect subsequent changes')) + ' |')
    return lines + ['']


def render_summary(root, data, report):
    """Compact reviewer queue and separate, unscored assistant issue proposals."""
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', '<br>')
    baseline = {}
    for kind, filename, id_key in [('scenario', 'scenarios.jsonl', 'scenario_id'),
                                   ('question', 'question_bank.jsonl', 'question_id')]:
        path = root / 'data/pilot_v0_1' / filename
        baseline[kind] = {row[id_key]: row for row in load_rows(path, 'pilot_reference', [])} if path.is_file() else {}
    def change_status(kind, row, id_key):
        original = baseline[kind].get(row[id_key])
        if original is None:
            return 'new' if baseline[kind] else 'pilot reference unavailable'
        changed = sorted(key for key in row if row.get(key) != original.get(key))
        return 'changed: ' + ', '.join(changed) if changed else 'retained revised pilot'
    proposals = []
    lines = ['# Exploratory review queue — ' + DATA.name, '',
             'Generated from JSONL. Assistant issue proposals below are not human decisions or scores.',
             'No source proposal is an approval. Effective approval is derived from the current-hash human decision log.',
             'Current approval counts: ' + packed(report['human_approval']['counts']) + '.',
             'Confirm realism and all six criteria, pilot-only clarification questions, previous_question availability,',
             'and model reuse terms. Splits are provisional; the test is not frozen or independently unseen.', '',
             '| Split | Scenarios |', '|---|---|']
    lines += [f'| {split} | {count} |' for split, count in sorted(report['splits'].items())]
    lines += ['', '## Scenarios', '', '| ID | Change from preserved pilot | Split / family | Category | Goal and activity | Assistant review issues |',
              '|---|---|---|---|---|---|']
    for row in data['scenarios']:
        codes = ['synthetic_realism_unverified']
        if row['context']['progress_status'] == 'unknown':
            codes.append('missingness_preserve_pilot_clarification')
        if row['category'] == 'contradictory_progress':
            count, total = row['context']['reported_completed_units'], row['context']['planned_units']
            codes.append('count_exceeds_plan_ambiguous_extra_work' if count is not None and total is not None and count > total
                         else 'conflict_preserve_pilot_clarification')
        if row['context']['previous_question'] is not None:
            codes.append('previous_question_interface_unconfirmed')
        if row['category'] == 'instruction_in_student_note':
            codes.append('untrusted_instruction_separate_safety_flag')
        proposals.append({'source': 'assistant_preparation', 'record_type': 'scenario',
                          'record_id': row['scenario_id'], 'status': 'proposed_issues_only', 'issue_codes': codes})
        lines.append('| ' + ' | '.join(cell(value) for value in (row['scenario_id'], change_status('scenario', row, 'scenario_id'),
            row['split'] + ' / ' + row['scenario_family_id'], row['category'],
            row['context']['learning_goal'] + ' ' + row['context']['planned_activity'], ', '.join(codes))) + ' |')
    lines += ['', 'See review.md for every original context value and evaluation-only acceptable behaviours.', '',
              '## Candidate question bank', '', '| ID | Change from preserved pilot | Question | Applicability | Exclusions |', '|---|---|---|---|---|']
    for row in data['questions']:
        codes = ['formal_human_approval_pending', 'applicability_requires_check']
        if row['reflection_focus'] in {'progress_clarification', 'record_clarification'}:
            codes.append('clarification_pilot_scope_only')
        proposals.append({'source': 'assistant_preparation', 'record_type': 'question',
                          'record_id': row['question_id'], 'status': 'proposed_issues_only', 'issue_codes': codes})
        lines.append('| ' + ' | '.join(cell(value) for value in
                     (row['question_id'], change_status('question', row, 'question_id'),
                      row['question_text'], row['applicable_when'], row['avoid_when'])) + ' |')
    duplicates = [flag for flag in report['data_quality_flags'] if flag['code'] == 'possible_near_duplicate_review']
    lines += ['', '## Duplicate review', '',
              f'{len(duplicates)} wording-similarity pairs flagged; exact duplicates are structural errors.',
              'Review the row pairs in validation_report.json. Related variants must stay within a family and split.',
              'Token Jaccard >= 0.72 or normalized sequence ratio >= 0.88; this misses semantic paraphrases.', '',
              'Use review_forms.jsonl for explicit human review, then record-reviews. Never submit assistant issue proposals.', '']
    lines += expanded_revision_sections(root, target_hashes(data), approval_states(target_hashes(data), data['decisions']))
    write_jsonl(root / REPORTS / 'assistant_review_proposals.jsonl', proposals)
    (root / REPORTS / 'review_summary.md').write_text('\n'.join(lines), encoding='utf-8')


def record_reviews(root, path):
    report, data, _ = validate(root)
    write_json(root / REPORTS / 'validation_report.json', report)
    require_valid(report)
    errors = []
    forms = load_rows(path, 'review_form', errors)
    if not forms:
        raise ValueError('no_review_forms')
    targets = target_hashes(data)
    for line, row in enumerate(forms, 1):
        validate_decision(row, 'review_form', line, errors, targets, form=True)
    if errors:
        # Errors contain fixed codes and line positions only.
        print(json.dumps(errors, indent=2))
        raise ValueError('invalid_review_forms_nothing_appended')
    latest = {(old['record_type'], old['record_id'], old['reviewer_code']): old
              for old in data['decisions']}
    batch_keys = set()
    for form in forms:
        key = (form['record_type'], form['record_id'], form['reviewer_code'])
        if key in batch_keys:
            raise ValueError('duplicate_target_in_review_batch_nothing_appended')
        batch_keys.add(key)
        old = latest.get(key)
        if old is not None and all(old.get(k) == v for k, v in form.items()):
            raise ValueError('duplicate_review_submission_nothing_appended')
    entries = [dict(form, review_id=str(uuid.uuid4())) for form in forms]
    # Local single-writer workflow. Append only; init/render never write this history.
    with (root / FILES['decisions']).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(''.join(packed(entry) + '\n' for entry in entries))


def export_inputs(root):
    # A failed rebuild must not leave a convenience pointer to an old export.
    (root / EXPORTS / 'latest.json').unlink(missing_ok=True)
    report, data, states = validate(root)
    write_json(root / REPORTS / 'validation_report.json', report)
    require_valid(report)
    if report['privacy_screening']['findings']:
        raise ValueError('privacy_findings_require_resolution_export_blocked')
    # Separate review gates from explicit feature allowlists; never copy an entire record.
    scenarios = [{'scenario_id': row['scenario_id'],
                  'context': {field: row['context'][field] for field in CONTEXT}}
                 for row in data['scenarios'] if states[('scenario', row['scenario_id'])] == 'accepted']
    questions = [{field: row[field] for field in QUESTION_EXPORT} for row in data['questions']
                 if states[('question', row['question_id'])] == 'accepted']
    destination = root / EXPORTS
    # Versioned by all source bytes: old exports cannot masquerade as the latest dataset.
    fingerprint = sha(packed({'input_sha256': report['input_sha256'],
                             'workflow_sha256': report['workflow_sha256']}).encode('utf-8'))
    bundle = destination / fingerprint
    bundle.mkdir(parents=True, exist_ok=True)
    write_jsonl(bundle / 'model_inputs.jsonl', scenarios)
    write_jsonl(bundle / 'retrieval_bank.jsonl', questions)
    manifest = {'dataset_fingerprint': fingerprint, 'input_sha256': report['input_sha256'],
                'workflow_sha256': report['workflow_sha256'],
                'raw_archive_sha256': ARCHIVE_SHA256, 'python_version': report['python_version'],
                'model_input_count': len(scenarios), 'retrieval_bank_count': len(questions),
                'output_sha256': {name: sha((bundle / name).read_bytes()) for name in
                                  ('model_inputs.jsonl', 'retrieval_bank.jsonl')}}
    write_json(bundle / 'manifest.json', manifest)
    write_json(destination / 'latest.json', {'bundle': fingerprint})
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'validate', 'review-docs', 'record-reviews', 'export'])
    parser.add_argument('--file', type=Path, help='Completed review forms (JSONL), for record-reviews only')
    parser.add_argument('--dataset', choices=['pilot_v0_1', 'exploratory_v0_2'], default='exploratory_v0_2',
                        help='CLI defaults to the expanded dataset; the earlier pilot is preserved.')
    args = parser.parse_args()
    configure_dataset(args.dataset)
    try:
        if args.command == 'init':
            initialize(ROOT)
            print('Initialized missing working files; existing data/review history preserved.')
        elif args.command == 'validate':
            report, _, _ = validate(ROOT)
            write_json(ROOT / REPORTS / 'validation_report.json', report)
            print('Structural validation:', report['structural_validation']['status'])
            print('Report:', REPORTS / 'validation_report.json')
            require_valid(report)
        elif args.command == 'review-docs':
            render_review(ROOT)
            print('Generated review.md, review_summary.md and review_forms.jsonl in', REPORTS)
        elif args.command == 'record-reviews':
            if args.file is None:
                parser.error('record-reviews requires --file')
            record_reviews(ROOT, args.file)
            print('Appended explicit human decisions; review history retained.')
        else:
            manifest = export_inputs(ROOT)
            print('Exported accepted scenarios:', manifest['model_input_count'])
            print('Exported accepted bank entries:', manifest['retrieval_bank_count'])
            print('Resolve', EXPORTS / 'latest.json', 'for the bundle. Pending records are excluded.')
    except (ValueError, OSError, zipfile.BadZipFile):
        # Do not print exception strings: filenames/content could contain sensitive text.
        print('Command failed. Check the validation report or fixed review error codes.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
