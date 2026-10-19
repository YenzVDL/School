"""Read-only verification and readable review augmentation of a saved development run.

No model calls or quality scores. Optional --directory selects an existing run;
otherwise use the latest run pointer. Never executes another experiment.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import research as r
import approaches as a
from ollama_local import QUESTION_SCHEMA
from scripts.run_development import development_material, schedule


def rows(path):
    errors = []
    result = r.load_rows(path,path.name,errors)
    if errors:
        raise ValueError('invalid_run_jsonl')
    return result


def verify(destination, root=r.ROOT):
    manifest = json.loads((destination/'manifest.json').read_text(encoding='utf-8'))
    if manifest['status']!='completed':
        raise ValueError('run_not_completed')
    for name,digest in manifest['artifact_sha256'].items():
        assert r.sha((destination/name).read_bytes())==digest, 'run_artifact_hash_mismatch'
    for name,digest in manifest['code_sha256'].items():
        snapshot = destination/'code_snapshot'/name
        source = snapshot if snapshot.is_file() else root/name
        assert r.sha(source.read_bytes())==digest, 'run_code_hash_mismatch'
    original = json.loads((destination/'repository_config.json').read_text(encoding='utf-8'))
    config = json.loads((destination/'effective_config.json').read_text(encoding='utf-8'))
    config_source = root/manifest.get('source_config','configs/experiment_v0_2.json')
    current = a.load_config(config_source)
    if 'source_config_sha256' in manifest:
        assert r.sha(config_source.read_bytes())==manifest['source_config_sha256']
    assert current==original and current['experiments_enabled'] is False
    expected_config = dict(original,experiments_enabled=True,status='authorized_development_execution')
    assert config==expected_config, 'unexpected_run_configuration_change'
    material,data,validation = development_material(root,config)
    assert material.current()
    assert validation['input_sha256']==manifest['source_input_sha256']
    assert set(manifest['development_ids'])==material.known_scenarios
    results = rows(destination/'results.jsonl')
    events = rows(destination/'api_events.jsonl')
    requests = rows(destination/'requests.jsonl')
    prepared = rows(destination/'prepared_requests.jsonl')
    failures = rows(destination/'failures.jsonl')
    expected_jobs = schedule(material.known_scenarios,config)
    assert [(row['scenario_id'],row['method'],row['seed']) for row in results]==expected_jobs
    assert len({row['output_id'] for row in results})==len(results)
    assert all(row['split']=='development' and row['scenario_id'] in material.known_scenarios for row in results)
    lookup = {row['output_id']:row for row in results}
    generated_ids = {row['output_id'] for row in results if row['method']!='fixed'}
    called_ids = {row['output_id'] for row in events}
    assert len(events)==len(requests)<=len(prepared)==len(generated_ids)==120
    assert called_ids<=generated_ids
    # Metadata/transport failure before /api/chat remains a recorded failed attempt.
    assert all(lookup[rid]['failure_code'] in {'generator_error','timeout','context_overflow'}
               for rid in generated_ids-called_ids)
    assert [row for row in results if row['failure_code'] or row['status'] not in {'selected','generated'}]==failures
    engine = a.ApproachEngine(material,config)
    metrics = []
    for event,request in zip(events,requests):
        assert event['request']==request['request']
        output = lookup[event['output_id']]
        body = event['request']
        intended = engine.prepare(output['scenario_id'],output['method'])['request']
        expected = dict(model=config['model']['selected'],stream=False,think=False,format=QUESTION_SCHEMA,keep_alive=0,
                        messages=[{'role':'system','content':intended.system},{'role':'user','content':intended.payload_json}],
                        options=dict(intended.options,seed=output['seed']))
        assert body==expected, 'actual_model_request_not_allowlisted_expected_prompt'
        # JSONL is canonicalized, so its parsed dict order differs from HTTP bytes.
        # Reconstruct the sender's insertion order before checking the byte hash.
        assert r.sha(json.dumps(expected).encode())==event['request_sha256']
        payload = json.loads(body['messages'][1]['content'])
        assert set(payload)==({'context','reference_questions'} if output['method']=='rag' else {'context'})
        assert set(payload['context'])==set(r.CONTEXT)
        for reference in payload.get('reference_questions',[]):
            assert set(reference)==set(r.QUESTION_EXPORT)
        if 'response' in event:
            response = event['response']
            assert response['model']==config['model']['selected']
            assert not response.get('message',{}).get('thinking')
            count = response.get('prompt_eval_count',0)
            assert 0 < count <= event['prompt_token_upper_bound']
            assert event['prompt_token_upper_bound']+body['options']['num_predict']<=body['options']['num_ctx']
            metrics.append(count)
            if output['raw_output'] is not None:
                assert output['raw_output']==response['message']['content']
        assert event['observed_chat_wall_seconds']>=0
    report = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),status='passed',
                  run_directory=destination.relative_to(root).as_posix(),
                  approved_counts=validation['human_approval']['counts'],
                  outputs_by_method=dict(Counter(row['method'] for row in results)),
                  model_calls=len(events),failures=len(failures),
                  development_scenarios=len(material.contexts),validation_scenarios_run=0,test_scenarios_run=0,
                  current_approvals_and_source_hashes_verified=True,actual_requests_match_allowlisted_preparation=True,
                  same_model_and_sampler_for_rag_direct=True,native_think_false_verified=True,
                  repository_configuration_unchanged=True,all_saved_artifact_hashes_verified=True,
                  prompt_budget_observation_max=max(metrics),prompt_budgets_verified=True,
                  quality_scores_assigned=False,independent_second_review=False)
    r.write_json(destination/'verification.json',report)
    r.write_json(root/'reports/exploratory_v0_2/development_run_verification.json',report)
    preparation_path = root/'reports/exploratory_v0_2/verification.json'
    preparation = json.loads(preparation_path.read_text(encoding='utf-8'))
    assert preparation['input_sha256']==validation['input_sha256']
    preparation.update(dataset_records_used_for_inference=len(material.contexts),
                       development_run_executed=True,development_model_calls=len(events),
                       comparison_run=True,final_comparison_run=False,
                       validation_scenarios_run=0,test_scenarios_run=0,
                       development_verification='development_run_verification.json',
                       development_verified_at_utc=report['checked_at_utc'])
    r.write_json(preparation_path,preparation)
    # Augment the generated blind review using its JSONL mapping, without exposing
    # method/seed labels or modifying results, prompts, settings or primary artifacts.
    mapping = rows(destination/'review_mapping.jsonl')
    review = (destination/'output_review.md').read_text(encoding='utf-8')
    for row in mapping:
        result = lookup[row['output_id']]
        raw = result['raw_output'] if result['raw_output'] is not None else '[No generated raw response; assess delivered wording]'
        heading = '## '+row['anonymous_id']+'\n'
        review = review.replace(heading,heading+'\nRaw output for separate human assessment:\n\n```text\n'+raw+'\n```\n',1)
    (destination/'output_review_with_raw.md').write_text(review,encoding='utf-8')
    r.write_json(destination/'review_supplement_manifest.json',{
        'generated_from':['results.jsonl','review_mapping.jsonl','output_review.md'],
        'quality_scores_assigned':False,
        'file_sha256':r.sha((destination/'output_review_with_raw.md').read_bytes())})
    # There is no Git repository: retain the exact executed source alongside its hashes.
    for name,digest in manifest['code_sha256'].items():
        snapshot = destination/'code_snapshot'/name
        if not snapshot.exists():
            snapshot.parent.mkdir(parents=True,exist_ok=True)
            snapshot.write_bytes((root/name).read_bytes())
        assert r.sha(snapshot.read_bytes())==digest
    print(json.dumps(report,indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path)
    args = parser.parse_args()
    destination = args.directory
    if destination is None:
        pointer = json.loads((r.ROOT/'reports/exploratory_v0_2/development_run_latest.json').read_text())
        destination = r.ROOT/pointer['directory']
    verify(destination.resolve())


if __name__=='__main__':
    main()
