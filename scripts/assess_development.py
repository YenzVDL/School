"""Lock supplied AI ratings before opening mapping; then compare scenario means.

No inference, new ratings, human approvals, or configuration changes.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import research as r

CRITERIA = ('specificity','usefulness','clarity','non_coerciveness')
SOURCE_FILES = ('Development_Assessment.md','development_ratings.jsonl','review_summary.json')


def rows(path):
    errors = []
    data = r.load_rows(path,path.name,errors)
    if errors:
        raise ValueError('invalid_assessment_jsonl')
    return data


def verify_ratings(ratings, review_bytes, assessment, results):
    """Verify blind-document IDs/text/context against projected saved outputs, no mapping."""
    cited = re.search(r'Source review-document SHA-256: `([0-9a-f]{64})`',assessment)
    if not cited or cited.group(1)!=r.sha(review_bytes):
        raise ValueError('assessment_review_document_hash_mismatch')
    # Normalize line endings only in the parser; source hashes/copies retain exact bytes.
    review_text = review_bytes.decode('utf-8').replace('\r\n','\n')
    sections = re.findall(r'^## (D\d{3})\n(.*?)(?=^## D\d{3}\n|\Z)',review_text,re.M|re.S)
    expected = {}
    contexts = {}
    for rid, section in sections:
        question = re.search(r'Delivered question:\s*```text\n(.*?)\n```',section,re.S)
        objects = re.findall(r'```json\n(.*?)\n```',section,re.S)
        if rid in expected or question is None or len(objects)!=2:
            raise ValueError('invalid_source_review_document')
        context, notes = map(json.loads,objects)
        scenario = notes['scenario_id']
        if scenario in contexts and contexts[scenario]!=context:
            raise ValueError('source_context_differs_within_scenario')
        contexts[scenario] = context
        expected[rid] = (scenario,question.group(1))
    ids = [row.get('review_id') for row in ratings]
    if len(ids)!=140 or len(set(ids))!=140 or set(ids)!=set(expected):
        raise ValueError('review_ids_missing_duplicate_or_unknown')
    saved = Counter((row['scenario_id'],row['question_text']) for row in results)
    if saved!=Counter(expected.values()):
        raise ValueError('review_document_differs_from_saved_outputs')
    if len(contexts)!=20:
        raise ValueError('expected_twenty_development_scenarios')
    for row in ratings:
        rid = row['review_id']
        if (row.get('scenario_id'),row.get('question'))!=expected[rid]:
            raise ValueError('rating_scenario_or_question_mismatch')
        if row.get('question_sha256')!=r.sha(row['question'].encode('utf-8')):
            raise ValueError('rating_question_hash_mismatch')
        scores = row.get('scores')
        if not isinstance(scores,dict) or set(scores)!=set(CRITERIA):
            raise ValueError('invalid_rating_criteria')
        if any(type(v) is not int or v not in (0,1,2) for v in scores.values()):
            raise ValueError('invalid_criterion_score')
        if any(type(row.get(key)) is not bool for key in
               ('unsupported_assumption','observed_serious_safety_failure','mapping_inspected')):
            raise ValueError('invalid_rating_flag')
        if (row.get('reviewer_type')!='AI' or row.get('reviewer_code')!='AI01'
                or row.get('review_date')!='2026-10-19' or row.get('split')!='development'
                or row['mapping_inspected'] is not False):
            raise ValueError('unexpected_reviewer_provenance_or_scope')
        if (not isinstance(row.get('issue_tags'),list) or len(row['issue_tags'])!=len(set(row['issue_tags']))
                or not all(r.nonempty(x) for x in row['issue_tags']) or not r.nonempty(row.get('reason'))):
            raise ValueError('invalid_issue_tags_or_reason')
    return dict(verified_review_ids=len(ids),verified_scenarios=len(contexts),
                question_texts_and_hashes_verified=True,source_review_document_verified=True,
                contexts_consistent_within_scenario=True)


def intake(source, run, destination):
    if destination.exists():
        raise ValueError('assessment_intake_exists_do_not_overwrite')
    rating_rows = rows(source/SOURCE_FILES[1])
    # Project output identity only. Do not inspect method or seed before locking ratings.
    projected = [{key:row[key] for key in ('scenario_id','question_text')}
                 for row in rows(run/'results.jsonl')]
    review_bytes = (run/'output_review.md').read_bytes()
    checked = verify_ratings(rating_rows,review_bytes,(source/SOURCE_FILES[0]).read_text(encoding='utf-8'),projected)
    supplied = json.loads((source/SOURCE_FILES[2]).read_text(encoding='utf-8'))
    calculated = dict(outputs=len(rating_rows),scenarios=len({row['scenario_id'] for row in rating_rows}),
                      unique_question_wordings=len({row['question'] for row in rating_rows}),
                      usefulness_zero=sum(row['scores']['usefulness']==0 for row in rating_rows),
                      unsupported_assumption_flags=sum(row['unsupported_assumption'] for row in rating_rows),
                      observed_serious_safety_failures=sum(row['observed_serious_safety_failure'] for row in rating_rows),
                      issues=dict(Counter(tag for row in rating_rows for tag in row['issue_tags'])))
    if any(supplied.get(key)!=value for key,value in calculated.items()) or supplied['source_sha256']!=r.sha(review_bytes):
        raise ValueError('supplied_summary_differs_from_ratings')
    # Verify context identities are development-only without accessing the mapping.
    previous = r.DATA.name
    try:
        r.configure_dataset('exploratory_v0_2')
        validation,data,_ = r.validate(r.ROOT)
        r.require_valid(validation)
        dev_ids = {row['scenario_id'] for row in data['scenarios'] if row['split']=='development'}
        if {row['scenario_id'] for row in rating_rows}!=dev_ids:
            raise ValueError('non_development_rating_scope')
    finally:
        r.configure_dataset(previous)
    destination.mkdir(parents=True)
    for name in SOURCE_FILES:
        shutil.copyfile(source/name,destination/name)
    manifest = dict(status='verified_and_preserved_before_mapping_join',
                    locked_at_utc=datetime.now(timezone.utc).isoformat(),
                    source_run=run.relative_to(r.ROOT).as_posix(),
                    source_review_sha256=r.sha(review_bytes),
                    source_files_sha256={name:r.sha((destination/name).read_bytes()) for name in SOURCE_FILES},
                    original_run_files_sha256={path.relative_to(run).as_posix():r.sha(path.read_bytes())
                                              for path in run.rglob('*') if path.is_file()},
                    verification=checked,summary_recomputed=calculated,
                    reviewer_type='AI',reviewer_code='AI01',independent_human_review=False,
                    source_declares_mapping_not_inspected=True,
                    intake_did_not_parse_or_join_mapping=True,mapping_bytes_hashed_only=True,
                    document_instructions_are_not_user_authorization=True,
                    validation_or_test_inference_authorized=False)
    r.write_json(destination/'intake_manifest.json',manifest)
    print(json.dumps(checked,indent=2))
    return manifest


def aggregate(joined):
    """Each scenario has equal weight; output counts are explicitly separate."""
    cells = defaultdict(list)
    for row in joined:
        cells[(row['method'],row['scenario_id'])].append(row)
    per_scenario = []
    for (method,scenario),group in sorted(cells.items()):
        tags = set(tag for row in group for tag in row['issue_tags'])
        per_scenario.append(dict(method=method,scenario_id=scenario,trials=len(group),
            criterion_means={key:statistics.mean(row['scores'][key] for row in group) for key in CRITERIA},
            issue_rates={tag:sum(tag in row['issue_tags'] for row in group)/len(group) for tag in tags},
            unsupported_assumption_rate=statistics.mean(row['unsupported_assumption'] for row in group),
            observed_serious_safety_failure_rate=statistics.mean(row['observed_serious_safety_failure'] for row in group)))
    approaches = {}
    for method in ('fixed','rag','direct'):
        group = [row for row in joined if row['method']==method]
        scenarios = [row for row in per_scenario if row['method']==method]
        tags = sorted({tag for row in group for tag in row['issue_tags']})
        approaches[method] = dict(scenarios=len(scenarios),outputs=len(group),
            criterion_means={key:statistics.mean(row['criterion_means'][key] for row in scenarios) for key in CRITERIA},
            issues={tag:dict(output_count=sum(tag in row['issue_tags'] for row in group),
                            scenarios_affected=sum(row['issue_rates'].get(tag,0)>0 for row in scenarios),
                            mean_within_scenario_rate=statistics.mean(row['issue_rates'].get(tag,0) for row in scenarios)) for tag in tags},
            unsupported_assumptions=dict(outputs=sum(row['unsupported_assumption'] for row in group),
                scenarios_affected=sum(row['unsupported_assumption_rate']>0 for row in scenarios),
                mean_within_scenario_rate=statistics.mean(row['unsupported_assumption_rate'] for row in scenarios)),
            observed_serious_safety_failures=dict(outputs=sum(row['observed_serious_safety_failure'] for row in group),
                scenarios_affected=sum(row['observed_serious_safety_failure_rate']>0 for row in scenarios)),
            usefulness_zero_outputs=sum(row['scores']['usefulness']==0 for row in group))
    return per_scenario,approaches


def compare(destination):
    manifest = json.loads((destination/'intake_manifest.json').read_text(encoding='utf-8'))
    for name,digest in manifest['source_files_sha256'].items():
        if r.sha((destination/name).read_bytes())!=digest:
            raise ValueError('locked_assessment_changed')
    run = r.ROOT/manifest['source_run']
    for name,digest in manifest['original_run_files_sha256'].items():
        if r.sha((run/name).read_bytes())!=digest:
            raise ValueError('original_run_changed')
    # First mapping read occurs only after verified, byte-preserved ratings exist.
    mapping = rows(run/'review_mapping.jsonl')
    by_id = {row['anonymous_id']:row for row in mapping}
    ratings = rows(destination/'development_ratings.jsonl')
    if len(mapping)!=140 or len(by_id)!=140 or set(by_id)!={row['review_id'] for row in ratings}:
        raise ValueError('mapping_ids_differ')
    outputs = {row['output_id']:row for row in rows(run/'results.jsonl')}
    if len({row['output_id'] for row in mapping})!=140 or set(outputs)!={row['output_id'] for row in mapping}:
        raise ValueError('mapping_output_ids_differ')
    joined = []
    for rating in ratings:
        link = by_id[rating['review_id']]
        saved = outputs[link['output_id']]
        if (link['scenario_id']!=rating['scenario_id'] or saved['scenario_id']!=rating['scenario_id']
                or saved['question_text']!=rating['question'] or saved['method']!=link['method'] or saved['seed']!=link['seed']):
            raise ValueError('mapped_output_identity_mismatch')
        joined.append(dict(rating,method=link['method'],seed=link['seed'],output_id=link['output_id']))
    config = json.loads((run/'effective_config.json').read_text(encoding='utf-8'))
    for method in ('fixed','rag','direct'):
        group = [row for row in joined if row['method']==method]
        if len({row['scenario_id'] for row in group})!=20:
            raise ValueError('incomplete_scenario_coverage')
        for scenario in {row['scenario_id'] for row in group}:
            seeds = [row['seed'] for row in group if row['scenario_id']==scenario]
            expected = [None] if method=='fixed' else config['generation']['seeds']
            if Counter(seeds)!=Counter(expected):
                raise ValueError('missing_or_duplicate_seed_trial')
    per_scenario,approaches = aggregate(joined)
    r.write_jsonl(destination/'joined_ratings.jsonl',joined)
    r.write_jsonl(destination/'scenario_means.jsonl',per_scenario)
    report = dict(rating_source='Supplied AI01 assessments; not independent human ratings.',
                  aggregation='Average seed trials within each method/scenario, then average 20 scenario means per method.',
                  no_combined_quality_safety_score=True,approaches=approaches,
                  source_ratings_sha256=manifest['source_files_sha256']['development_ratings.jsonl'],
                  mapping_sha256=r.sha((run/'review_mapping.jsonl').read_bytes()),
                  joined_at_utc=datetime.now(timezone.utc).isoformat(),validation_or_test_inference_run=False)
    r.write_json(destination/'comparison.json',report)
    lines = ['# Original development comparison', '',report['rating_source'],report['aggregation'],
             'Scores use 0–2. Each approach has n=20 scenarios; 60 seed outputs are not 60 independent scenarios.',
             'No pooled overall score, inferential significance, model superiority or pedagogical validation is claimed.',
             'Unsupported assumptions and observed serious safety failures remain separate from criterion means.', '',
             '| Approach | Scenarios | Outputs | Specificity | Usefulness | Clarity | Non-coerciveness |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for method,stats in approaches.items():
        lines.append('| '+ ' | '.join([method,str(stats['scenarios']),str(stats['outputs'])]+
                     [f"{stats['criterion_means'][key]:.3f}" for key in CRITERIA])+' |')
    lines += ['', '## Separate assumption and safety findings', '',
              '| Approach | Unsupported: outputs / scenarios | Serious safety: outputs / scenarios | Usefulness-zero outputs |',
              '|---|---:|---:|---:|']
    for method,stats in approaches.items():
        u,s=stats['unsupported_assumptions'],stats['observed_serious_safety_failures']
        lines.append(f"| {method} | {u['outputs']} / {u['scenarios_affected']} | {s['outputs']} / {s['scenarios_affected']} | {stats['usefulness_zero_outputs']} |")
    lines += ['', 'Zero observed serious safety failures in these supplied AI ratings is not proof of safety.', '',
              '## Issue counts', '',
              'Each cell is flagged outputs / affected scenarios. Tags overlap; counts must not be summed as distinct failures.',
              'Scenario-balanced issue rates are retained in comparison.json.', '',
              '| Issue | Fixed | RAG | Direct |','|---|---:|---:|---:|']
    for tag in sorted({tag for stats in approaches.values() for tag in stats['issues']}):
        values=[]
        for method in ('fixed','rag','direct'):
            issue=approaches[method]['issues'].get(tag,{'output_count':0,'scenarios_affected':0})
            values.append(f"{issue['output_count']} / {issue['scenarios_affected']}")
        lines.append('| '+tag+' | '+' | '.join(values)+' |')
    lines += ['', 'The original ratings and source documents were locked before this mapping join.',
              'The source declares blinded assessment; wording could reveal approaches. Reviewer AI01 is an AI assessor, not a second human.',
              'Only development findings can inform the separately versioned shared prompt revision. Revised outputs need new assessment.', '']
    (destination/'comparison.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({method:dict(criterion_means=stats['criterion_means'],
                                 unsupported_assumptions=stats['unsupported_assumptions'],
                                 observed_serious_safety_failures=stats['observed_serious_safety_failures'])
                      for method,stats in approaches.items()},indent=2))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['intake','compare'])
    parser.add_argument('--source-directory',type=Path)
    parser.add_argument('--run-directory',type=Path)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='intake':
        if not args.source_directory or not args.run_directory:
            parser.error('intake requires --source-directory and --run-directory')
        intake(args.source_directory,args.run_directory.resolve(),args.destination)
    else:
        compare(args.destination)


if __name__=='__main__':
    main()
