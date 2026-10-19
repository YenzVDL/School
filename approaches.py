"""Three approaches with one configurable, locally pinned generator.

The CLI only checks preparation. Generative execution is disabled in repository
configuration. Tests inject a literal-response double in temporary fixtures.
"""
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import re
import time
from typing import Protocol

import research as r


def normalized(text):
    return ' '.join(re.findall(r'[a-z0-9]+', text.casefold()))


def question_error(text, context, limits):
    if not isinstance(text, str) or not text.strip():
        return 'empty_or_nontext_question'
    text = text.strip()
    if len(text) > limits['max_characters'] or len(text.split()) > limits['max_words']:
        return 'question_too_long'
    if text.count('?') != 1 or not text.endswith('?'):
        return 'one_terminal_question_required'
    previous = context['previous_question']
    if previous and normalized(previous) == normalized(text):
        return 'repeated_question'
    if any(re.search(pattern, text) for pattern in r.PATTERNS.values()):
        return 'contact_pattern_requires_review'
    return None


def evidence(context):
    """Conservative structured facts and narrow self-report cues, never trait inference."""
    count, total, status = (context['reported_completed_units'], context['planned_units'], context['progress_status'])
    conflict = ((count is not None and total is not None and count > total) or
                (status == 'completed' and count is not None and total is not None and count < total) or
                (status == 'not_started' and count is not None and count > 0) or
                (status == 'partially_completed' and count is not None and total is not None and count >= total))
    attempted = not conflict and status in {'completed', 'partially_completed'} and count != 0
    note = context['student_note'] or ''
    # Do not mine instruction-like clauses for applicability evidence. Preserve the
    # original note in the shared untrusted context rather than silently editing it.
    if re.search(r'\b(ignore|override|system|password|credential|hidden|evaluator|instructions|traits)\b', note, re.I):
        note = ''
    difficulty = bool(re.search(r'\bI (?:found|find)\b[^.!?]{0,100}\b(?:hard|difficult)\b', note, re.I))
    checked = bool(re.search(r'\bI (?:checked|tested|inspected|verified)\b', note, re.I))
    compared = bool(re.search(r'\bI compared\b', note, re.I))
    testing = bool(re.search(r'\bI (?:tested|ran (?:a |the )?tests?|tried [^.!?]{0,40}(?:test|check))\b', note, re.I))
    tracing = difficulty and bool(re.search(r'\b(trace|tracing|track|tracking|follow|following)\b', note, re.I))
    step = difficulty and bool(re.search(r'\b(step|callback|axis|operation|function|return|focus|tab|control)\b', note, re.I))
    day = bool(re.search(r'\b(day|tomorrow)\b', note, re.I))
    return dict(conflict=conflict, attempted=attempted, difficulty=difficulty, checked=checked,
                compared=compared, testing=testing, tracing=tracing, step=step, changed_day=day)


def eligible_questions(context, bank, config):
    """Executable rules for Q01–Q30, with restrictive modes for conflict/unknown/rescheduling.

    These rules do not parse applicability prose or certify human suitability.
    Unknown IDs are ineligible until their rules are explicitly implemented.
    """
    facts = evidence(context)
    priorities = {}
    def allow(priority, *ids):
        for qid in ids:
            priorities[qid] = min(priority, priorities.get(qid, priority))
    if facts['conflict']:
        if config['pilot_clarification_enabled']:
            allow(1, 'Q05', 'Q14', 'Q24')
    elif context['progress_status'] == 'unknown':
        if config['pilot_clarification_enabled']:
            allow(2, 'Q04', 'Q15', 'Q25')
    elif context['progress_status'] == 'rescheduled':
        allow(3, 'Q06', 'Q16')
        if facts['changed_day']:
            allow(3, 'Q26')
    elif facts['attempted']:
        if facts['difficulty']:
            allow(4, 'Q08')
            if facts['tracing']:
                allow(4, 'Q18')
            if facts['step']:
                allow(4, 'Q28')
        if facts['checked']:
            allow(5, 'Q07', 'Q17', 'Q27')
        planned, actual = context['planned_minutes'], context['reported_minutes']
        if planned is not None and actual is not None and actual > 0:
            allow(6 if planned != actual else 8, 'Q03')
        if actual is not None and actual > 0:
            allow(8, 'Q13')
        if planned is not None or actual is not None:
            allow(8, 'Q23')
        if facts['compared']:
            allow(7, 'Q21')
        allow(8, 'Q01', 'Q02', 'Q09', 'Q10', 'Q11', 'Q12', 'Q19', 'Q22', 'Q29', 'Q30')
        if facts['testing']:
            allow(8, 'Q20')
    eligible = [copy.deepcopy(row) for row in bank if row['question_id'] in priorities
                and question_error(row['question_text'], context, config['output_format']) is None]
    return sorted(eligible, key=lambda row: (priorities[row['question_id']], row['question_id']))


def retrieve(context, eligible, settings):
    stopwords = set(settings['stopwords'])
    def tokens(text):
        return set(normalized(text).split()) - stopwords
    query = tokens(' '.join(context[field] for field in settings['query_fields']))
    scored = []
    for row in eligible:
        terms = tokens(' '.join(row[field] for field in settings['index_fields']))
        union = query | terms
        score = len(query & terms) / len(union) if union else 0.0
        scored.append((row, score))
    backoff = bool(scored) and not any(score > 0 for _, score in scored)
    if not backoff:
        scored.sort(key=lambda item: (-item[1], item[0]['question_id']))
    chosen = scored[:settings['top_k']]
    return [row for row, _ in chosen], [dict(question_id=row['question_id'], score=score) for row, score in chosen], backoff


@dataclass
class Material:
    root: Path
    dataset: str
    hashes: dict
    known_scenarios: set
    contexts: dict
    bank: list

    def current(self):
        return all((self.root / name).is_file() and r.sha((self.root / name).read_bytes()) == digest
                   for name, digest in self.hashes.items())


def load_material(root=r.ROOT, dataset='exploratory_v0_2'):
    previous = r.DATA.name
    try:
        r.configure_dataset(dataset)
        report, data, states = r.validate(root)
        r.require_valid(report)
        if report['privacy_screening']['findings']:
            raise ValueError('privacy_findings_block_preparation')
        contexts = {row['scenario_id']: {field: copy.deepcopy(row['context'][field]) for field in r.CONTEXT}
                    for row in data['scenarios'] if states[('scenario', row['scenario_id'])] == 'accepted'}
        bank = [{field: row[field] for field in r.QUESTION_EXPORT} for row in data['questions']
                if states[('question', row['question_id'])] == 'accepted']
        return Material(Path(root), dataset, report['input_sha256'],
                        {row['scenario_id'] for row in data['scenarios']}, contexts, bank)
    finally:
        r.configure_dataset(previous)


@dataclass(frozen=True)
class GenerationRequest:
    model: str | None
    artifact_digest: str | None
    system: str
    payload_json: str
    options: dict
    timeout_seconds: int
    think: bool = False


class Generator(Protocol):
    def generate(self, request: GenerationRequest) -> str:
        """Honor the pinned request and token budget; never pull weights or truncate data."""


class ContextOverflowError(Exception):
    """A backend's selected-model tokenizer found that the request will not fit."""


def load_config(path=None):
    path = path or r.ROOT / 'configs/experiment_v0_2.json'
    config = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=r.no_repeated_keys,
                        parse_constant=r.reject_constant)
    return validate_config(config)


def validate_config(config):
    model = config['model']
    expected = {'selected', 'artifact_digest', 'recommended_candidate', 'selection_status',
                'same_artifact_for_rag_and_direct'}
    if set(model) != expected or model['same_artifact_for_rag_and_direct'] is not True:
        raise ValueError('one_shared_base_model_required')
    selected, digest = model['selected'], model['artifact_digest']
    if selected is None:
        if digest is not None:
            raise ValueError('unselected_model_cannot_have_a_selected_digest')
    elif (not isinstance(selected, str) or not selected.strip() or not isinstance(digest, str)
          or re.fullmatch(r'[0-9a-f]{64}', digest) is None):
        raise ValueError('selected_model_requires_resolved_artifact_digest')
    if type(config['experiments_enabled']) is not bool or type(config['pilot_clarification_enabled']) is not bool:
        raise ValueError('explicit_execution_and_scope_flags_required')
    if config['rules_version'] != 'conservative_0.1':
        raise ValueError('unsupported_rules_version')
    retrieval = config['retrieval']
    if (retrieval['algorithm'] != 'lowercase_alphanumeric_token_jaccard' or
            retrieval['query_fields'] != ['learning_goal', 'planned_activity'] or
            retrieval['index_fields'] != ['question_text', 'reflection_focus'] or
            retrieval['applicability_filter_first'] is not True or
            type(retrieval['top_k']) is not int or retrieval['top_k'] <= 0):
        raise ValueError('unsupported_or_unsafe_retrieval_configuration')
    if config['output_format']['required_keys'] != ['question_text']:
        raise ValueError('unsupported_output_contract')
    for key in ('max_words', 'max_characters', 'terminal_question_marks'):
        value = config['output_format'][key]
        if type(value) is not int or value <= 0:
            raise ValueError('invalid_output_limits')
    if config['output_format']['terminal_question_marks'] != 1:
        raise ValueError('one_question_required')
    for key in ('num_ctx', 'num_predict', 'timeout_seconds', 'parallel_requests'):
        value = config['generation'][key]
        if type(value) is not int or value <= 0:
            raise ValueError('invalid_generation_setting')
    if config['generation']['automatic_retries'] != 0 or config['generation']['parallel_requests'] != 1:
        raise ValueError('implementation_supports_sequential_no_retry_protocol_only')
    if config['generation'].get('think') is not False:
        raise ValueError('explicit_api_think_false_required')
    return config


class ApproachEngine:
    def __init__(self, material, config, generator: Generator | None = None):
        self.material = material
        self.config = copy.deepcopy(validate_config(config))
        self.generator = generator  # No automatic provider discovery or weight download.

    def prepare(self, scenario_id, method):
        if method not in {'fixed', 'rag', 'direct'}:
            raise ValueError('unknown_approach')
        base = dict(scenario_id=scenario_id, method=method, status='prepared', request=None,
                    eligible=[], retrieval_scores=[], zero_score_rule_backoff=False)
        if not self.material.current():
            return dict(base, status='stale_material_reload_required')
        if scenario_id not in self.material.known_scenarios:
            return dict(base, status='unknown_scenario')
        if scenario_id not in self.material.contexts:
            return dict(base, status='scenario_approval_required')
        context = copy.deepcopy(self.material.contexts[scenario_id])
        eligible = eligible_questions(context, self.material.bank, self.config)
        base['eligible'] = eligible
        if method in {'fixed', 'rag'} and not eligible:
            return dict(base, status='no_suitable_approved_question')
        if method == 'fixed':
            return base
        payload = {'context': {key: context[key] for key in r.CONTEXT}}
        system = self.config['shared_system_constraints']
        if method == 'rag':
            selected, scores, backoff = retrieve(context, eligible, self.config['retrieval'])
            payload['reference_questions'] = [{key: row[key] for key in r.QUESTION_EXPORT} for row in selected]
            base['retrieval_scores'], base['zero_score_rule_backoff'] = scores, backoff
            system += '\n' + self.config['rag_addition']
        generation = self.config['generation']
        options = {key: generation[key] for key in ('temperature', 'top_p', 'top_k', 'min_p', 'num_ctx', 'num_predict')}
        model = self.config['model']
        base['request'] = GenerationRequest(model['selected'], model['artifact_digest'], system,
                                             r.packed(payload), options, generation['timeout_seconds'], think=generation['think'])
        return base

    def run(self, scenario_id, method, seed=20261019):
        started = time.perf_counter()
        prepared = self.prepare(scenario_id, method)
        result = dict(scenario_id=scenario_id, method=method, status=prepared['status'], question_text=None,
                      question_id=None, raw_output=None, failure_code=None, fallback_used=False,
                      retrieval_scores=prepared['retrieval_scores'],
                      zero_score_rule_backoff=prepared['zero_score_rule_backoff'],
                      model=self.config['model']['selected'] if method != 'fixed' else None,
                      artifact_digest=self.config['model']['artifact_digest'] if method != 'fixed' else None,
                      config_sha256=r.sha(r.packed(self.config).encode('utf-8')),
                      implementation_sha256=r.sha(Path(__file__).read_bytes()), seed=seed,
                      model_call_seconds=None)
        def finish():
            result['elapsed_seconds'] = time.perf_counter() - started
            return result
        if result['status'] != 'prepared':
            return finish()
        if method == 'fixed':
            row = prepared['eligible'][0]
            result.update(status='selected', question_text=row['question_text'], question_id=row['question_id'])
            return finish()
        if not self.config['experiments_enabled']:
            result['status'] = 'generation_disabled'
            return finish()
        model = self.config['model']
        if (not isinstance(model['selected'], str) or not model['selected'].strip() or
                not isinstance(model['artifact_digest'], str) or
                re.fullmatch(r'[0-9a-f]{64}', model['artifact_digest']) is None):
            result['status'] = 'base_model_selection_required'
            return finish()
        if self.generator is None or self.config['generator']['backend'] == 'disabled':
            result['status'] = 'generator_backend_required'
            return finish()
        if seed not in self.config['generation']['seeds']:
            result['status'] = 'unconfigured_seed'
            return finish()
        request = prepared['request']
        request = GenerationRequest(request.model, request.artifact_digest, request.system, request.payload_json,
                                    dict(request.options, seed=seed), request.timeout_seconds, think=request.think)
        call_started = time.perf_counter()
        try:
            raw = self.generator.generate(request)
        except ContextOverflowError:
            result['model_call_seconds'] = time.perf_counter() - call_started
            failure = 'context_overflow'
        except TimeoutError:
            result['model_call_seconds'] = time.perf_counter() - call_started
            failure = 'timeout'
        except Exception:
            result['model_call_seconds'] = time.perf_counter() - call_started
            failure = 'generator_error'  # Never echo backend error strings or matched content.
        else:
            result['model_call_seconds'] = time.perf_counter() - call_started
            result['raw_output'] = raw
            try:
                output = json.loads(raw, object_pairs_hook=r.no_repeated_keys, parse_constant=r.reject_constant)
                if not isinstance(output, dict) or set(output) != {'question_text'}:
                    raise ValueError()
            except (ValueError, TypeError):
                failure = 'invalid_output_json_contract'
            else:
                failure = question_error(output['question_text'], self.material.contexts[scenario_id], self.config['output_format'])
                if failure is None:
                    result.update(status='generated', question_text=output['question_text'].strip())
        if failure:
            result['failure_code'] = failure
            if prepared['eligible']:
                row = prepared['eligible'][0]
                result.update(status='fallback', fallback_used=True, question_text=row['question_text'],
                              question_id=row['question_id'])
            else:
                result['status'] = 'abstained'
        return finish()


def main():
    """Readiness check only: this CLI never executes an approach or calls a generator."""
    config = load_config()
    material = load_material()
    report = dict(status='model_independent_implementation_only',
                  known_scenarios=len(material.known_scenarios), accepted_scenarios=len(material.contexts),
                  accepted_bank_entries=len(material.bank), base_model_selected=config['model']['selected'],
                  experiments_enabled=config['experiments_enabled'], backend=config['generator']['backend'],
                  methods=['fixed', 'rag', 'direct'], model_calls=0,
                  base_model_selection_is_not_approach_selection=True)
    r.write_json(r.ROOT / 'reports/approach_implementation.json', report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
