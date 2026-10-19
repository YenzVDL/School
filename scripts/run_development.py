"""Explicit development-only run. No validation/test execution or automatic tuning."""
import argparse
from collections import Counter
import copy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import research as r
import approaches as a
from local_token_budget import QwenAsciiBudget
from ollama_local import LocalOllamaClient, LocalOllamaGenerator


def append(path, row):
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(r.packed(row) + '\n')


def development_material(root, config):
    previous = r.DATA.name
    try:
        r.configure_dataset(config['dataset'])
        report, data, states = r.validate(root)
        r.require_valid(report)
        ids = {row['scenario_id'] for row in data['scenarios'] if row['split'] == 'development'}
        material = a.load_material(root, config['dataset'])
        if not ids or not ids <= material.contexts.keys() or not material.bank:
            raise ValueError('all_development_scenarios_and_bank_require_current_approval')
        material.known_scenarios = ids
        material.contexts = {rid: material.contexts[rid] for rid in sorted(ids)}
        return material, data, report
    finally:
        r.configure_dataset(previous)


def schedule(ids, config):
    fixed = [(rid, 'fixed', None) for rid in sorted(ids)]
    generated = [(rid, method, seed) for rid in sorted(ids) for method in ('rag','direct')
                 for seed in config['generation']['seeds']]
    random.Random(config['shuffle_seed']).shuffle(generated)
    return fixed + generated


class CapturedClient(LocalOllamaClient):
    def __init__(self, config, destination):
        super().__init__(config['runtime']['base_url'], config['generation']['timeout_seconds'])
        self.destination, self.job, self.bound = destination, None, None
        self.calls = 0

    def call(self, path, body=None):
        if path != '/api/chat':
            return super().call(path, body)
        event = dict(output_id=self.job, request=body,
                     request_sha256=r.sha(json.dumps(body).encode('utf-8')), prompt_token_upper_bound=self.bound)
        append(self.destination/'requests.jsonl', event)
        start = time.perf_counter()
        self.calls += 1
        try:
            response = super().call(path, body)
            event['response'] = response
            return response
        except Exception as exc:
            # Do not put response snippets, contact matches or raw exception text in logs.
            event['transport_failure'] = 'timeout' if isinstance(exc, TimeoutError) else 'local_transport_error'
            raise
        finally:
            event['observed_chat_wall_seconds'] = time.perf_counter()-start
            append(self.destination/'api_events.jsonl', event)


class BudgetedGenerator:
    def __init__(self, backend, budget, client, destination):
        self.backend, self.budget, self.client, self.destination = backend, budget, client, destination

    def generate(self, request):
        bound = self.budget.check(request)
        self.client.bound = bound
        append(self.destination/'prepared_requests.jsonl', dict(output_id=self.client.job,
               request=asdict(request), prompt_token_upper_bound=bound,
               serialized_request_sha256=r.sha(r.packed(asdict(request)).encode('utf-8'))))
        return self.backend.generate(request)


def render_outputs(destination, results, material, data, config, review_prefix='D'):
    """Review-only join. Evaluation notes are never supplied to a generator."""
    notes = {row['scenario_id']: row for row in data['notes']}
    rows = list(results)
    random.Random(config['shuffle_seed']).shuffle(rows)
    mapping = []
    lines = ['# Development output review', '',
             'Generated from saved JSONL. Development only; no validation/test inference.',
             'No quality scores or output approvals have been assigned. Review each output independently.',
             'Data approval by R01 is AI-assisted human review, not an independent second review or output-quality endorsement.',
             'Method/seed/status mapping is separate in review_mapping.jsonl; do not inspect it before blinded assessment.',
             'Identical or fallback wording may still reveal a method. Blinding is imperfect.',
             'Evaluation notes below are human-review material only. Never ingest this document into a model/index.',
             'Assess clarity, specificity, usefulness, autonomy, unsupported assumptions and safety; note missing/conflicting input handling.', '']
    for index, result in enumerate(rows,1):
        anonymous = f'{review_prefix}{index:03}'
        mapping.append(dict(anonymous_id=anonymous,output_id=result['output_id'],scenario_id=result['scenario_id'],
                            method=result['method'],seed=result['seed'],status=result['status'],failure_code=result['failure_code']))
        lines += [f'## {anonymous}', '', 'Approved development context:', '', '```json',
                  json.dumps(material.contexts[result['scenario_id']],indent=2), '```', '',
                  'Delivered question:', '', '```text', result['question_text'] or '[No question delivered]', '```', '',
                  'Evaluation-only guidance (illustration is not a gold answer):', '', '```json',
                  json.dumps(notes[result['scenario_id']],indent=2), '```', '',
                  'Human observations: __. Unsupported assumptions: __. Safety concerns: __.',
                  'Quality ratings: unscored. Reviewer/date: __.', '']
    r.write_jsonl(destination/'review_mapping.jsonl',mapping)
    (destination/'output_review.md').write_text('\n'.join(lines),encoding='utf-8')


def summarize(results, calls):
    methods = {}
    for method in ('fixed','rag','direct'):
        rows = [row for row in results if row['method']==method]
        elapsed = [row['elapsed_seconds'] for row in rows]
        model = [row['model_call_seconds'] for row in rows if row['model_call_seconds'] is not None]
        methods[method] = dict(outputs=len(rows),status_counts=dict(Counter(row['status'] for row in rows)),
                              failure_counts=dict(Counter(row['failure_code'] for row in rows if row['failure_code'])),
                              fallback_count=sum(row['fallback_used'] for row in rows),
                              elapsed_seconds=dict(min=min(elapsed),median=statistics.median(elapsed),max=max(elapsed)) if elapsed else None,
                              model_call_seconds=dict(min=min(model),median=statistics.median(model),max=max(model)) if model else None)
    return dict(methods=methods,model_calls=calls,development_scenarios=len({row['scenario_id'] for row in results}),
                validation_scenarios_run=0,test_scenarios_run=0,quality_scores_assigned=False,
                inference_scope='approved development only',automatic_config_changes_from_outputs=False)


def run(root=r.ROOT, config_path=None, review_prefix='D'):
    if review_prefix not in {'D','P'}:
        raise ValueError('unsupported_review_prefix')
    config_path = Path(config_path).resolve() if config_path else root/'configs/experiment_v0_2.json'
    config = a.load_config(config_path)
    material, data, report = development_material(root,config)
    jobs = schedule(material.known_scenarios,config)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = root/'runs'/('development_'+stamp+'_'+uuid.uuid4().hex[:8])
    destination.mkdir(parents=True)
    original_config = copy.deepcopy(config)
    # This explicit command implements this session's development-only authorization.
    # The repository default remains disabled; sampler/prompts/rules do not change.
    config['experiments_enabled'] = True
    config['status'] = 'authorized_development_execution'
    r.write_json(destination/'repository_config.json',original_config)
    r.write_json(destination/'effective_config.json',config)
    client = CapturedClient(config,destination)
    if client.call('/api/version')['version'] != config['runtime']['version']:
        raise ValueError('runtime_version_changed')
    if client.model(config['model']['selected'])['digest'] != config['model']['artifact_digest']:
        raise ValueError('model_digest_changed')
    if r.sha(Path(config['runtime']['executable']).read_bytes()) != config['runtime']['executable_sha256']:
        raise ValueError('runtime_executable_changed')
    shown = client.call('/api/show',{'model':config['model']['selected'],'verbose':True})
    if r.sha(shown['template'].encode()) != config['runtime']['template_sha256']:
        raise ValueError('chat_template_changed')
    budget = QwenAsciiBudget(shown['model_info'])
    engine = a.ApproachEngine(material,config,BudgetedGenerator(LocalOllamaGenerator(config,client),budget,client,destination))
    # Preflight every distinct request before any development inference, without sending it.
    bounds = {}
    for rid in sorted(material.known_scenarios):
        for method in ('rag','direct'):
            request = engine.prepare(rid,method)['request']
            if request:
                bounds[rid+'/'+method] = budget.check(request)
    manifest = dict(started_at_utc=datetime.now(timezone.utc).isoformat(),status='running',
                    authorization='Explicit user authorization: R01-approved development only; validation/test forbidden.',
                    review_basis='Single human R01 review supported by AI-assisted proposals; not independent second review.',
                    dataset=config['dataset'],source_input_sha256=report['input_sha256'],
                    source_config=config_path.relative_to(root).as_posix(),
                    source_config_sha256=r.sha(config_path.read_bytes()),review_id_prefix=review_prefix,
                    development_ids=sorted(material.known_scenarios),planned_outputs=len(jobs),
                    generation_seeds=config['generation']['seeds'],fixed_runs_per_scenario=1,
                    generation_runs_per_method_per_scenario=len(config['generation']['seeds']),
                    prompt_token_upper_bounds=bounds,template_allowance_tokens=64,
                    warmup_calls=0,keep_alive=0,latency_note='Includes per-call model loading/unloading; not a warm-throughput benchmark.',
                    code_sha256={name:r.sha((root/name).read_bytes()) for name in
                                 ('research.py','approaches.py','ollama_local.py','local_token_budget.py','scripts/run_development.py')},
                    no_quality_scores=True)
    r.write_json(destination/'manifest.json',manifest)
    results = []
    print('Run directory: '+str(destination),flush=True)
    for index,(rid,method,seed) in enumerate(jobs,1):
        client.job = f'O{index:03}'
        result = engine.run(rid,method,seed if seed is not None else config['generation']['seeds'][0])
        if method=='fixed':
            result['seed'] = None
        result.update(output_id=client.job,split='development')
        append(destination/'results.jsonl',result)
        if result['failure_code'] or result['status'] not in {'selected','generated'}:
            append(destination/'failures.jsonl',result)
        results.append(result)
        print(json.dumps(dict(completed=index,total=len(jobs),scenario_id=rid,method=method,seed=seed,
                              status=result['status'],failure_code=result['failure_code'],
                              elapsed_seconds=round(result['elapsed_seconds'],3))),flush=True)
    (destination/'failures.jsonl').touch(exist_ok=True)
    summary = summarize(results,client.calls)
    r.write_json(destination/'summary.json',summary)
    render_outputs(destination,results,material,data,config,review_prefix)
    manifest.update(status='completed',completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    artifact_sha256={path.name:r.sha(path.read_bytes()) for path in destination.iterdir()
                                     if path.is_file() and path.name!='manifest.json'})
    r.write_json(destination/'manifest.json',manifest)
    r.write_json(root/'reports/exploratory_v0_2/development_run_latest.json',dict(directory=destination.relative_to(root).as_posix(),summary=summary))
    print(json.dumps(summary,indent=2),flush=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-development',action='store_true',help='Explicitly execute only approved development scenarios')
    parser.add_argument('--config',type=Path,help='Explicit versioned configuration; repository default is preserved')
    parser.add_argument('--review-prefix',choices=['D','P'],default='D',help='Anonymous review ID prefix')
    args = parser.parse_args()
    if not args.run_development:
        parser.error('Use --run-development only with explicit development inference authorization.')
    run(config_path=args.config,review_prefix=args.review_prefix)


if __name__=='__main__':
    main()
