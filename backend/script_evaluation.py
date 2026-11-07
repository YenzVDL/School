"""Versioned batch orchestration; content scoring lives in fixed_rules_v3."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from . import fixed_rules_v3 as rules

VERSION = rules.VERSION
CRITERIA = rules.DIMENSIONS
RULES = rules.DEFINITIONS


def implementation_hash():
    root = Path(__file__).parent
    files = ['script_evaluation.py', 'fixed_rules_v3.py', 'schema.py']
    return hashlib.sha256(b''.join(name.encode()+b'\0'+(root/name).read_bytes() for name in files)).hexdigest()


def fingerprint(outputs):
    fields = ['id','version','scenario_version_id','question','status','method','model','condition_id','repetition']
    pairs = [{**{k:o.get(k) for k in fields}, 'inputs':rules.clean_inputs(o.get('inputs'))} for o in outputs]
    return hashlib.sha256(json.dumps(sorted(pairs,key=lambda o:o['id']),sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def evaluate_pair(output):
    inputs=rules.clean_inputs(output.get('inputs'))
    question=output.get('question') or ''
    result=rules.score(question,inputs)
    failed=output.get('status')!='completed' or not question.strip()
    if failed:
        for name,c in result['criteria'].items():
            if name!='format' or not question.strip():
                c['status']='skipped'
                c['explanation']='Content assessment unavailable for missing output or execution failure.'
        for c in result['checks']:
            if c['criterion_id']!='format' or not question.strip() and c['rule_id']!='format.nonempty.v1':
                c['status']='skipped'
        result['review_state']='execution_failure'
        result['reason']='Execution status: '+str(output.get('status'))
    pair_hash=hashlib.sha256(json.dumps({'inputs':inputs,'question':question},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {**result,'output_id':output.get('id'),'output_version':output.get('version'),
            'scenario_version_id':output.get('scenario_version_id'),'inputs':inputs,'question':question,'pair_hash':pair_hash,
            'execution_status':output.get('status'),'status':'skipped' if failed else 'flag' if any(c['status']=='flag' for c in result['criteria'].values()) else 'inconclusive'}


def aggregate(rows):
    counts=Counter(r['status'] for r in rows)
    criteria={}
    for name in CRITERIA:
        values=Counter(r['criteria'][name]['status'] for r in rows)
        n=values['pass']+values['flag']+values['inconclusive']
        decisive=values['pass']+values['flag']
        criteria[name]={'evaluated':n,**{k:values[k] for k in ['pass','flag','inconclusive','skipped']},
                        'decision_coverage':decisive/n if n else None,
                        'violation_rate_per_evaluated':values['flag']/n if n else None,
                        'denominator':n}
    valid=[r for r in rows if r['execution_status']=='completed' and r['question'].strip()]
    present=[r for r in rows if r['question'].strip()]
    overlap=[r['measurements']['context_token_precision'] for r in valid if r['measurements']['context_token_precision'] is not None]
    grouped={}
    for row in valid: grouped.setdefault(rules.normalized(row['question']),[]).append(row)
    duplicates=[{'normalized_text':key,'count':len(items),'output_ids':[r['output_id'] for r in items],
                 'scenario_version_ids':sorted({r['scenario_version_id'] for r in items if r['scenario_version_id']}),
                 'cross_scenario':len({r['scenario_version_id'] for r in items})>1} for key,items in grouped.items() if len(items)>1]
    compliant=sum(r['criteria']['format']['status']=='pass' for r in present)
    per_rule={}
    for r in rows:
        for check in r['checks']:
            count=per_rule.setdefault(check['rule_id'],{'criterion_id':check['criterion_id'],'pass':0,'flag':0,'inconclusive':0,'skipped':0})
            count[check['status']]+=1
    return {'total':len(rows),'evaluated':len(valid),'criteria':criteria,'statuses':{k:counts[k] for k in ['pass','flag','inconclusive','skipped']},
            'operational':{'planned':len(rows),'successful':len(valid),'execution_failures':len(rows)-len(valid),
                           'nonempty_outputs':len(present),'format_checked':len(present),'format_compliant':compliant,
                           'format_rate_per_present':compliant/len(present) if present else None,'format_rate_per_planned':compliant/len(rows) if rows else None},
            'format_pass_rate':compliant/len(present) if present else None,
            'context_token_precision_mean':sum(overlap)/len(overlap) if overlap else None,
            'unique_question_count':len(grouped),'exact_unique_raw_count':len({r['question'] for r in valid}),
            'diversity':{'normalized_unique_count':len(grouped),'exact_unique_raw_count':len({r['question'] for r in valid}),
                         'normalized_duplicates':duplicates,'repetition_rate':(len(valid)-len(grouped))/len(valid) if valid else None,
                         'cross_scenario_reuse_groups':sum(d['cross_scenario'] for d in duplicates),'interpretation':'Descriptive reuse, never an individual quality penalty or uniqueness reward.'},
            'word_count':{'mean':sum(r['measurements']['word_count'] for r in valid)/len(valid) if valid else None,
                          'minimum':min((r['measurements']['word_count'] for r in valid),default=None),'maximum':max((r['measurements']['word_count'] for r in valid),default=None)},
            'rule_counts':per_rule,'semantic_quality':{'reviewed':0,'unreviewed':len(valid),'source':'No semantic judgment in fixed scripts'}}


def evaluate(outputs):
    rows=[];groups={}
    for output in outputs:
        row=evaluate_pair(output)
        row.update(method=output.get('method'),model=output.get('model'),condition_id=output.get('condition_id'),repetition=output.get('repetition',1))
        rows.append(row)
        groups.setdefault((row['method'] or 'unknown',row['model'] or 'Not applicable',row['condition_id'] or ''),[]).append(row)
    case=lambda r:(r['scenario_version_id'],r['repetition'])
    sets=[{case(r) for r in subset if r['scenario_version_id']} for subset in groups.values()]
    common=set.intersection(*sets) if sets else set()
    return {'version':VERSION,'implementation_hash':implementation_hash(),'source':'fixed_scripts','batch_hash':fingerprint(outputs),
            'rules':RULES,'rule_versions':{c['rule_id']:c['rule_version'] for r in rows for c in r['checks']},
            **aggregate(rows),'pairs':rows,'by_condition':[{'method':key[0],'model':key[1],'condition_id':key[2] or None,**aggregate(items),
                 'matched_cases':aggregate([r for r in items if case(r) in common])} for key,items in sorted(groups.items())],
            'comparison':{'common_scenario_repetitions':len(common),'condition_count':len(groups),'same_case_sets':bool(sets) and all(s==sets[0] for s in sets),
                          'policy':'Identical scenario versions and repetitions; failed cases retained in planned denominators. Provenance is attached only after content scoring. No overall quality score or winner.'},
            'notice':'V3 measures scoped mechanical checks and conservative textual patterns. Semantic quality remains unreviewed. Inconclusive is never a pass or a failure.'}


def ready(job, outputs):
    return (job.get('kind')=='experiment' and job.get('status') in ['completed','completed_with_errors'] and bool(outputs)
            and len(outputs)==job.get('total') and not any(o.get('status') in ['pending','running','evaluating','interrupted'] for o in outputs))


def records(store, job):
    return collect_records(job,store.all('script_assessments'))


def collect_records(job, stored=()):
    result={}
    for report in job.get('script_assessment_history',[])+([job['script_assessment']] if job.get('script_assessment') else [])+list(stored):
        if report.get('job_id',job['id'])==job['id']:
            result[report['id']]=report
    return sorted(result.values(),key=lambda r:(r.get('created_at',''),r['id']))


def save(store, job_id):
    from .store import now,uid
    with store.connect():
        job=store.get('jobs',job_id)
        outputs=[o for o in store.all('outputs') if o['job_id']==job_id]
        if not ready(job,outputs): raise ValueError('Finish collecting every planned output before running fixed metrics')
        for existing in records(store,job):
            if existing['version']==VERSION and existing.get('implementation_hash')==implementation_hash() and existing['batch_hash']==fingerprint(outputs):return existing
        result={**evaluate(outputs),'id':uid('script_assessment'),'job_id':job_id,'created_at':now(),
                'dataset_snapshot_id':job.get('dataset_snapshot_id'),'bank_snapshot_id':job.get('bank_snapshot_id')}
        store.put('script_assessments',result,insert=True)
        return result


def report(job, outputs, assessments=()):
    reports=collect_records(job,assessments)
    current=[r for r in reports if r['version']==VERSION]
    latest=current[-1] if current else None
    stale=bool(latest and (latest.get('implementation_hash')!=implementation_hash() or latest['batch_hash']!=fingerprint(outputs)))
    state='stale' if stale else 'completed' if latest else 'ready' if ready(job,outputs) else 'collecting'
    return {'can_run':ready(job,outputs),'status':state,'result':latest,'version':VERSION,'rules':RULES,'reports':reports}
