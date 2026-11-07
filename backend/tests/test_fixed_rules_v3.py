"""Observed regressions and boundaries; expected results are scoped to rules."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from backend.fixed_rules_v3 import score, VERSION
from backend import script_evaluation as scripts
from backend.main import create_app
from fastapi.testclient import TestClient
from .conftest import approved_inputs, wait_job


def scenario(**changes):
    return {'learning_goal':'Learn Python unit testing','planned_activity':'Write Python unit tests',
            'progress':{'planned_units':4,'completed_units':2,'unit':'steps'},
            'planned_time':{'value':20,'unit':'minutes'},'reported_time':{'value':35,'unit':'minutes'},**changes}


def check(result, prefix):
    return [r for r in result['checks'] if r['rule_id'].startswith(prefix)]


@pytest.mark.parametrize('question,expected',[
    ('Why did you spend only 15 minutes on this activity?', 'flag'),
    ('Why did you spend 35 minutes on this activity?', 'pass'),
    ('What might explain why you recorded 15 minutes?', 'flag'),
    ('Could you spend 15 minutes on practice next time?', 'inconclusive'),
    ('What might happen if you spent 15 minutes on a future activity?', 'inconclusive'),
    ('Why did you record 2100 seconds?', 'pass'),
    ('Why did you record 0.5 hours?', 'flag'),
    ('What would you change, given that you recorded 15 minutes?', 'flag'),
])
def test_recorded_time_claims_and_hypothetical_alternatives(question,expected):
    """Actual durations use normalized structured evidence; future alternatives are not past assertions."""
    result=score(question,scenario())
    time_checks=check(result,'facts.numeric_reported_time')+check(result,'facts.hypothetical_time')
    assert time_checks and time_checks[0]['status']==expected


def test_observed_15_minute_hallucination_retains_evidence():
    question='What might explain the delay, given that the student has only recorded 15 minutes of actual work?'
    finding=check(score(question,scenario()),'facts.numeric_reported_time')[0]
    assert finding['status']=='flag'
    assert finding['evidence']['claimed_normalized']==900
    assert finding['evidence']['recorded_normalized']==2100
    assert 'reported_time' in finding['scenario_fields']


@pytest.mark.parametrize('question,classification',[
    ('What is a boundary unit test for an empty list in Python?','technical_knowledge_or_recall'),
    ('What is the default TCP port for HTTPS?','technical_knowledge_or_recall'),
    ('What is one possible reason why the SQL query plan changed?','ambiguous'),
    ('What would you record about your progress to help you plan your next ICT learning step?','planning_next_steps'),
    ('What led you to select that port when configuring the HTTPS service?','decisions_approaches'),
])
def test_structure_not_keyword_quality(question,classification):
    """Query-plan keywords are not learner reflection; explicit learner syntax is only a structural indicator."""
    result=score(question,scenario())
    assert result['classification']==classification
    c=result['criteria']['reflection_structure']
    assert c['requires_semantic_judgment'] and c['metric_version']==VERSION
    assert 'usefulness' not in result['criteria']


def test_unsupported_technology_and_prospective_suggestion_differ():
    """An invented current Python context is unsupported; suggesting a new option needs relevance review."""
    inputs={'learning_goal':'Inspect encryption','planned_activity':'Inspect a local network service configuration'}
    assert check(score('What is a common approach for inspecting this configuration in Python?',inputs),'context.technology_python')[0]['status']=='flag'
    assert check(score('Could you try Python for a future investigation?',inputs),'context.technology_python')[0]['status']=='inconclusive'


def test_valid_reflection_structure_does_not_establish_semantic_quality():
    result=score('What would you record about your progress to help you plan your next ICT learning step?',scenario(progress=None))
    assert result['criteria']['format']['status']=='pass'
    assert result['criteria']['reflection_structure']['status']=='pass'
    assert not any(c['status']=='flag' for c in result['checks'])
    assert result['semantic_quality']['status']=='unreviewed'
    assert result['review_state']=='requires_review'


def test_unknown_progress_does_not_support_failure():
    """Unknown progress is not failed performance."""
    result=score('Why did you fail to complete the activity?',scenario(progress=None))
    assert check(result,'facts.premise_performance')[0]['status']=='flag'


def test_conflicting_progress_sources_are_not_resolved_by_fiat():
    """Both numeric 2/4 and note all-four are preserved; neither proves the completion premise."""
    result=score('How did you complete all four steps?',scenario(student_note='I completed all four planned steps.'))
    assert result['evidence_conflicts']==['progress']
    assert check(result,'facts.completed_task')[0]['status']=='inconclusive'
    assert check(result,'facts.quantity_completed_units')[0]['status']=='inconclusive'
    assert not any(c['status']=='flag' for c in result['checks'] if c['criterion_id']=='factual_grounding')


def test_paraphrase_without_overlap_is_not_irrelevance():
    """A lexical vocabulary gap cannot prove semantic irrelevance."""
    result=score('Which approach would you revisit?',{'learning_goal':'Design data storage','planned_activity':'Sketch tables'})
    assert result['measurements']['context_token_precision']==0
    assert result['criteria']['contextual_grounding']['status']=='inconclusive'


def test_bank_reuse_is_descriptive_not_an_individual_penalty():
    """Independent scenarios may legitimately share the same bank question."""
    rows=[{'id':str(n),'version':1,'scenario_version_id':str(n),'status':'completed','method':'fixed','inputs':scenario(),'question':'Which Python approach would you practice next?'} for n in range(3)]
    result=scripts.evaluate(rows)
    assert result['diversity']['normalized_unique_count']==1
    assert result['diversity']['cross_scenario_reuse_groups']==1
    assert result['diversity']['repetition_rate']==pytest.approx(2/3)
    assert result['pairs'][0]['criteria']==result['pairs'][1]['criteria']


@pytest.mark.parametrize('question', ['What would you record next?', 'Why did you fail to complete all four steps?', 'What is Python?'])
def test_all_checks_are_strictly_method_blind(question):
    """Provenance, retrieval, priority and labels are not scorer inputs."""
    original={'id':'same','version':1,'status':'completed','inputs':scenario(),'question':question}
    expected=scripts.evaluate_pair(original)
    for method in ['fixed','rag','constrained']:
        other={**original,'method':method,'model':'different','trace':{'conditions':{'missing':['progress']},'retrieved':[{'score':999}]},'origin':'approved','labels':{'quality':4},'priority':999}
        assert scripts.evaluate_pair(other)==expected


def test_previous_question_normalization_format_checks_and_language_limits():
    result=score('What would you try next?',scenario(previous_question='  WHAT would you  try next? '))
    assert check(result,'format.previous_nonrepetition')[0]['status']=='flag'
    assert check(result,'format.language')[0]['status']=='inconclusive'
    assert check(score('Reflection question: What would you try next?',scenario()),'format.no_extra_response')[0]['status']=='flag'
    assert score('In Python, which example would you inspect?',scenario())['criteria']['format']['status']=='pass'
    assert check(score('Welke aanpak wil je proberen?',scenario()),'format.no_extra_response')[0]['status']=='inconclusive'


def test_raw_invalid_question_remains_in_format_denominator():
    """Observed trailing quotes fail format even though content scoring is skipped."""
    rows=[{'id':'ok','version':1,'status':'completed','question':'What would you try next?','inputs':scenario()},
          {'id':'bad','version':1,'status':'invalid','question':'"What would you try next?"','inputs':scenario()}]
    result=scripts.evaluate(rows)
    assert result['operational']['format_checked']==2
    assert result['operational']['format_compliant']==1
    assert result['format_pass_rate']==.5
    assert result['criteria']['reflection_structure']['skipped']==1


def test_every_rule_has_auditable_provenance():
    for rule in score('Why did you record 15 minutes?',scenario())['checks']:
        assert all(k in rule for k in ['criterion_id','metric_version','status','evidence','explanation','scenario_fields','rule_id','rule_version','deterministic','requires_semantic_judgment'])


def test_duration_comparisons_use_normalized_units():
    """Thirty minutes is shorter than a one-hour plan, regardless of the stored unit labels."""
    inputs=scenario(planned_time={'value':1,'unit':'hours'},reported_time={'value':30,'unit':'minutes'})
    assert check(score('Why did you spend longer than planned?',inputs),'facts.duration_comparison')[0]['status']=='flag'
    assert check(score('Why did you spend less time than planned?',inputs),'facts.duration_comparison')[0]['status']=='pass'


def test_progress_quantities_are_role_and_unit_specific():
    assert check(score('Why did you record three of the four steps?',scenario()),'facts.numeric_progress_completed_units')[0]['status']=='flag'
    assert check(score('Why did you record two of the four steps?',scenario()),'facts.numeric_progress_completed_units')[0]['status']=='pass'
    assert check(score('Why did you record three tests?',scenario()),'facts.progress_unit_unresolved')[0]['status']=='inconclusive'


def test_recorded_control_assessments_and_inferred_labels_are_not_interchangeable():
    """An inferred or reference answer alone cannot support a claim about the student's recorded correctness."""
    inputs=scenario(control_results=[{'question':'What is double(3)?','student_answer':'6','reference_answer':'6','recorded_assessment':'Correct'}])
    assert check(score('How would you explain your recorded correct answer?',inputs),'facts.control_correct')[0]['status']=='pass'
    inputs['control_results'][0].update(recorded_assessment=None,ai_inferred_assessment='incorrect')
    assert check(score('Why was your incorrect answer different?',inputs),'facts.control_incorrect')[0]['status']=='flag'


def test_hypothetical_emotions_and_explicit_recorded_decisions():
    """Future hypotheticals do not assert emotions; a past selection needs recorded evidence."""
    assert not check(score('What could you try if you were frustrated?',scenario()),'facts.premise_emotion')
    assert check(score('How did you overcome your anxiety?',scenario()),'facts.premise_emotion')[0]['status']=='flag'
    q='What led you to select that port when configuring the HTTPS service?'
    assert check(score(q,scenario()),'facts.premise_selection')[0]['status']=='flag'
    assert check(score(q,scenario(student_note='I selected port 443.')),'facts.premise_selection')[0]['status']=='pass'


def test_word_budget_boundary_and_previous_question_context_reference():
    q='What '+' '.join(['example']*38)+' next?'
    assert check(score(q,scenario()),'format.word_budget')[0]['status']=='pass'
    assert check(score(q.replace(' next?',' another next?'),scenario()),'format.word_budget')[0]['status']=='flag'
    result=score('Which part of your previous reflection question would you revisit?',scenario(previous_question='What would you try next?'))
    assert check(result,'context.reference_previous_question')[0]['status']=='pass'


def test_new_reports_append_without_rewriting_original_job_or_legacy_report(lab):
    s,r,p,jobs=lab
    *_,ds,bank=approved_inputs(r)
    j=jobs.create_experiment({'name':'Immutable','dataset_snapshot_id':ds['id'],'bank_snapshot_id':bank['id'],'methods':['fixed']})
    wait_job(s,j['id'])
    old={'id':'old-report','job_id':j['id'],'version':'fixed-rubric-v2-method-blind','implementation_hash':'old-hash','batch_hash':'old-batch','created_at':'2020','pairs':[]}
    s.patch('jobs',j['id'],script_assessment=old)
    before=copy.deepcopy(s.get('jobs',j['id']))
    report=scripts.save(s,j['id'])
    assert s.get('jobs',j['id'])==before
    assert scripts.records(s,before)==[old,report]
    for fn in [lambda:s.patch('script_assessments',report['id'],version='tampered'), lambda:s.delete('script_assessments',report['id'])]:
        with pytest.raises(ValueError,match='immutable'):fn()
    assert s.get('script_assessments',report['id'])==report
    with TestClient(create_app(s,p)) as client:
        assert client.get('/api/script-evaluations/old-report/export').json()==old
        export=client.get('/api/jobs/'+j['id']+'/export').json()
        assert export['job']==before and export['script_evaluations']==[old,report]
    assert not p.calls


def test_original_v2_implementation_archive_hash_is_unchanged():
    root=Path('backend/legacy_metrics/v2')
    names=['script_evaluation.py','question_metrics.py','methods.py','schema.py','scenario_generation.py']
    actual=hashlib.sha256(b''.join(n.encode()+b'\0'+(root/n).read_bytes() for n in names)).hexdigest()
    assert actual==json.loads((root/'manifest.json').read_text())['implementation_hash']
