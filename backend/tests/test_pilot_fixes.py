import copy
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from backend import model_policy, scenario_generation, bank_questions, experiment_preflight, methods, bank_diagnostics
from backend.main import create_app
from backend.provider import Ollama, Cancelled
from backend.metrics import report
from .conftest import approved_inputs, wait_job


def judgment():
    return {'context_fit':{'value':'Yes','explanation':'ICT activity match','context':'Available ICT activity'}, 'usefulness':{'value':'Yes','explanation':'Invites reflection on a learning choice','context':'Open approach question'}, 'correctness':{'value':'No','explanation':'Claims completion without evidence','context':'No completion evidence supplied'}}


def response(text, runtime=None):
    return {'text':text,'runtime':runtime or {'done_reason':'stop'},'latency_seconds':.01,'request':{'capture_source':'TEST FIXTURE','payload':{'response':text}},'effective_settings':{'think':False}}


def test_artifact_identity_and_short_thinking_policy():
    thinking = {'name':'qwen3:4b','thinking':{'values':[True],'default':True},'capabilities':['thinking'], 'model_info':{'general.finetune':'Thinking','general.version':'2507'}}
    assert model_policy.describe(thinking)['variant'] == 'thinking-only'
    with pytest.raises(ValueError,match='Unsupported|cannot disable'):
        model_policy.validate_research(thinking, {'think':False,'num_predict':128})
    with pytest.raises(ValueError,match='incompatible'):
        model_policy.validate_research(thinking, {'think':None,'num_predict':128})
    with pytest.raises(ValueError,match='1024'):
        model_policy.validate_research(thinking, {'think':True,'num_predict':128},'thinking')
    assert model_policy.validate_research(thinking, {'think':True,'num_predict':2048},'thinking')['artifact_version'] == '2507'
    hybrid = {**thinking,'model_info':{},'thinking':{'values':[False,True],'default':True}}
    with pytest.raises(ValueError,match='explicit think=false'):
        model_policy.validate_research(hybrid, {'think':None})
    assert model_policy.validate_research(hybrid, {'think':False})['variant'] == 'hybrid'


def test_actual_research_provider_serializes_verified_thinking_control(monkeypatch):
    observed = []
    def transport(request):
        if request.url.path == '/api/tags':
            return httpx.Response(200,json={'models':[{'name':'fixture:hybrid','digest':'stable'}]})
        if request.url.path == '/api/show':
            return httpx.Response(200,json={'thinking':{'values':[False,True],'default':True},'capabilities':['completion','thinking']})
        payload = json.loads(request.content); observed.append(payload)
        return httpx.Response(200,text=json.dumps({'thinking':'internal trace','response':'','done':False})+'\n'+json.dumps({'response':'Which approach would you like to try?','done':True,'done_reason':'stop','eval_count':12}))
    sync, async_client = httpx.Client, httpx.AsyncClient
    monkeypatch.setattr(httpx,'Client',lambda **kw:sync(transport=httpx.MockTransport(transport),**kw))
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:async_client(transport=httpx.MockTransport(transport),**kw))
    result = Ollama().generate('fixture:hybrid',methods.SYSTEM,'actual research context',{'think':False,'num_predict':128,'_model_digest':'stable'},lambda:False)
    assert observed[0]['system'] == methods.SYSTEM and observed[0]['think'] is False and observed[0]['stream'] is True
    assert result['text'] == 'Which approach would you like to try?' and 'internal' not in result['text']
    assert result['diagnostics']['thinking_characters'] > 0 and result['runtime']['eval_count'] == 12
    assert result['request']['payload'] == observed[0]


@pytest.mark.parametrize('text,runtime,status',[('',{'done_reason':'length','eval_count':128},'output_limit_before_answer'),('',{'done_reason':'stop'},'empty_final_answer'),('How would',{'done_reason':'length'},'truncated'),('One? Two?',{'done_reason':'stop'},'invalid')])
def test_final_failure_classification_and_no_fictional_ai_judgment(lab,text,runtime,status):
    s,r,p,jobs = lab
    *_,ds,bank = approved_inputs(r)
    p.generate=lambda *a,**kw: response(text,runtime)
    job=jobs.create_experiment({'name':'Failure classification','dataset_snapshot_id':ds['id'],'methods':['constrained'],'models':['test-fixture-model'],'ai_control':False,'evaluator_model':'test-fixture-model'})
    wait_job(s,job['id'])
    output=next(o for o in s.all('outputs') if o['job_id']==job['id'])
    assert output['status']==status and output['generation_runtime']==runtime
    assert not s.all('labels')


def test_preflight_is_actual_path_separate_and_bound_to_exact_config(lab):
    s,r,p,jobs=lab
    *_,ds,bank=approved_inputs(r)
    cfg={'name':'Batch','dataset_snapshot_id':ds['id'],'methods':['constrained'],'models':['test-fixture-model'],'repetitions':11}
    with pytest.raises(ValueError,match='preflight'):
        jobs.create_experiment(cfg)
    check=experiment_preflight.run(jobs,cfg)
    assert check['passed'] and p.calls[0]['system']==methods.SYSTEM
    assert not s.all('outputs') and not s.all('labels')
    jobs.schedule=lambda _:None
    queued=jobs.create_experiment({**cfg,'preflight_id':check['id']})
    assert queued['total']==11
    with pytest.raises(ValueError,match='differ'):
        jobs.create_experiment({**cfg,'settings':{'temperature':.5},'preflight_id':check['id']})


def test_plan_topic_variation_missing_schema_duplicate_retry_and_summary(lab):
    s,r,p,jobs=lab
    dataset=r.dataset('Planned fixtures')
    calls=[]
    first={'learning_goal':'Understand SQL joins','planned_activity':'Write SQL queries joining two tables','progress':None}
    second={'learning_goal':'Understand REST APIs','planned_activity':'Implement a Flask REST API endpoint','progress':None}
    def generate(model,system,prompt,settings,cancel,**kw):
        calls.append((prompt,kw['response_schema']))
        return response(json.dumps(first if len(calls)<=2 else second))
    p.generate=generate
    job=jobs.scenario_task('generation',{'dataset_id':dataset['id'],'model':'test-fixture-model','count':2,'topics':['databases and SQL','web development and APIs'],'variations':['missing information']})
    final=wait_job(s,job['id'])
    assert final['status']=='completed' and final['done']==2 and len(calls)==3
    assert all(schema['properties']['progress']=={'type':'null'} for _,schema in calls)
    assert 'assigned_topic_and_variation' in calls[0][0] and 'existing_scenario_reference_data' in calls[1][0]
    assert 'Exact duplicate Inputs' in calls[2][0]
    assert final['generation_summary']['duplicate_rejections']==1
    assert final['generation_summary']['actual_topic_coverage']['databases and SQL']==1
    assert all(s.get('scenarios',key)['inputs']['progress'] is None for key in final['results'])


def test_semantic_warnings_keep_unknowns_and_intentional_conflicts_visible():
    inputs={'learning_goal':'Understand REST APIs','planned_activity':'Write an API','control_results':[{'question':None,'student_answer':None,'recorded_assessment':'Endpoint returns 200 OK'}],'previous_question':'How do you handle HTTP status codes?','progress':{'planned_units':5,'completed_units':2},'student_note':'I completed all steps'}
    before=copy.deepcopy(inputs)
    warnings=scenario_generation.validate_plan(inputs,{'topic':'web development and APIs','variation':'contradictory information'})
    assert any('functionality' in w for w in warnings) and any('previous_question' in w for w in warnings) and any('Intentional' in w for w in warnings)
    assert inputs==before


def test_conditions_numeric_comparisons_time_units_control_and_specificity():
    inputs={'progress':{'planned_units':5,'completed_units':2,'unit':'tests'},'planned_time':{'value':1,'unit':'hours'},'reported_time':{'value':70,'unit':'minutes'},'control_results':[{'question':'What does SQL SELECT do?','student_answer':'Deletes rows','recorded_assessment':'incorrect'}]}
    conditions={'compare':[{'left':'reported_time.value','op':'gt','right':'planned_time.value'}],'control_assessment':'incorrect'}
    assert methods.matches(conditions,inputs)
    assert not methods.matches(conditions,{**inputs,'reported_time':None})
    assert not methods.matches(conditions,{**inputs,'reported_time':{'value':'70','unit':'minutes'}})
    assert not methods.matches(conditions,{**inputs,'control_results':[{'recorded_assessment':'incorrect'}]})
    assert methods.specificity({'conditions':{'present':['planned_time']}})==methods.specificity({'conditions':{'present':['planned_time','planned_time.value','planned_time.unit']}})
    assert not methods.matches({'compare':[{'left':'progress.completed_units','op':'gte','right':'progress.planned_units'}]},inputs)
    with pytest.raises(ValueError,match='Comparisons support'):
        bank_questions.validate({'text':'Which approach might you try?','conditions':{'compare':[{'left':'student_note','op':'gt','right':'planned_time.value'}]}})


def test_rag_ignores_json_keys_generic_tags_and_inapplicable_questions():
    def q(identifier,text,conditions=None):
        return {'id':identifier,'question_id':identifier,'text':text,'tags':['planned_time','student_note','SQL'],'conditions':conditions or {}}
    bank=[q('time','How might you plan time for the next learning step?'),q('sql','Which SQL query approach would help you understand joins?'),q('wrong','Which SQL query approach helped correct your answer?',{'control_assessment':'incorrect'})]
    inputs={'learning_goal':'Understand SQL joins','planned_activity':'Write a SQL query joining tables','student_note':'Comparing SQL join approaches','planned_time':{'value':45,'unit':'minutes'}}
    matches=methods.retrieve(inputs,bank,3)
    assert [m['version_id'] for m in matches]==['sql']
    assert methods.retrieve({'planned_time':{'value':45,'unit':'minutes'}},bank,3)==[]
    trace=methods.prepare('rag',inputs,bank)
    assert 'planned_time' not in trace['retrieval_settings']['query_text']
    assert trace['retrieval_settings']['version']==methods.RETRIEVAL_VERSION


def saved_experiment(lab, count=2):
    s,r,p,jobs=lab
    *_,ds,bank=approved_inputs(r)
    job=jobs.create_experiment({'name':'Existing immutable outputs','dataset_snapshot_id':ds['id'],'bank_snapshot_id':bank['id'],'methods':['fixed'],'repetitions':count})
    wait_job(s,job['id'])
    return job, [o for o in s.all('outputs') if o['job_id']==job['id']]


def test_script_evaluation_preserves_outputs_labels_and_snapshots(lab):
    from backend.script_evaluation import save
    s,r,p,jobs=lab
    experiment,outputs=saved_experiment(lab)
    preserved=copy.deepcopy(outputs)
    snapshots=copy.deepcopy(s.all('snapshots'))
    result=save(s,experiment['id'])
    assert result['evaluated']==2 and result['source']=='fixed_scripts'
    assert s.all('outputs')==preserved and s.all('snapshots')==snapshots
    assert not p.calls and not s.all('labels')
    with TestClient(create_app(s,p)) as client:
        exported=client.get('/api/jobs/'+experiment['id']+'/export').json()
        assert exported['script_evaluations']==[result]
        assert 'script_assessment' not in exported['job']
        assert exported['metrics']['script_evaluation']['result']==result
        for path in ['/api/evaluation/jobs','/api/evaluation/calibrate']:
            assert client.post(path,json={'source_job_id':experiment['id'],'model':'test-fixture-model'}).status_code==422
    assert not p.calls


def test_script_evaluation_keeps_execution_failures_out_of_quality_counts(lab):
    from backend.script_evaluation import save
    s,r,p,jobs=lab
    experiment,outputs=saved_experiment(lab)
    s.patch('outputs',outputs[1]['id'],status='failed',question=None)
    result=save(s,experiment['id'])
    assert result['evaluated']==1 and result['statuses']['skipped']==1
    assert result['total']==2
    assert all(c['evaluated']==1 for c in result['criteria'].values())
    assert not p.calls and not s.all('labels')


def test_script_evaluation_requires_complete_collection(lab):
    from backend.script_evaluation import save
    s,r,p,jobs=lab
    experiment,outputs=saved_experiment(lab)
    s.patch('jobs',experiment['id'],status='running')
    with pytest.raises(ValueError,match='Finish collecting'):
        save(s,experiment['id'])
    s.patch('jobs',experiment['id'],status='completed')
    s.patch('outputs',outputs[1]['id'],status='pending')
    with pytest.raises(ValueError,match='Finish collecting'):
        save(s,experiment['id'])
    s.patch('outputs',outputs[1]['id'],status='completed')
    assert save(s,experiment['id'])['evaluated']==2
    assert not p.calls


def test_no_human_quality_or_agreement_is_not_assessed_and_concentration_visible(lab):
    s,r,p,jobs=lab
    experiment,outputs=saved_experiment(lab)
    metrics=report(outputs,[],s.get('jobs',experiment['id']))
    assert metrics['quality']['human']['overall']['end_to_end_acceptance'] is None
    assert metrics['quality']['human']['overall']['assessment_status']=='Not assessed'
    assert metrics['evaluator_accuracy']['correctness']['macro_f1'] is None
    assert metrics['concentration']['fixed_top_share']==1
    diagnostic=bank_diagnostics.inspect(s.get('snapshots',experiment['bank_snapshot_id'])['records'],s.get('snapshots',experiment['dataset_snapshot_id'])['records'])
    assert len(diagnostic['unconditional_versions'])==1 and diagnostic['selection_frequencies']


def test_inline_ai_evaluation_and_preflight_are_rejected_before_inference(lab):
    s,r,p,jobs=lab
    *_,ds,bank=approved_inputs(r)
    cfg={'name':'No AI judging','dataset_snapshot_id':ds['id'],'methods':['constrained'],'models':['test-fixture-model'],'ai_control':True,'evaluator_model':'test-fixture-model'}
    with pytest.raises(ValueError,match='AI evaluation is disabled'):
        jobs.create_experiment(cfg)
    with pytest.raises(ValueError,match='AI evaluation is disabled'):
        experiment_preflight.run(jobs,cfg)
    assert not p.calls and not s.all('outputs')


def test_script_evaluation_is_idempotent_and_survives_reload(lab):
    from backend.script_evaluation import save
    from backend.store import Store
    s,r,p,jobs=lab
    experiment,outputs=saved_experiment(lab,1)
    first=save(s,experiment['id'])
    assert save(Store(s.path),experiment['id'])==first
    assert s.all('script_assessments')==[first]
    assert 'script_assessment_history' not in s.get('jobs',experiment['id'])
    assert not p.calls


def test_ai_evaluation_entry_points_are_disabled(lab):
    s,r,p,jobs=lab
    for action in [lambda:jobs.calibrate({'model':'test-fixture-model'}), lambda:jobs.evaluation_task({}), lambda:jobs._assess(None,{},'test-fixture-model',{})]:
        with pytest.raises(ValueError,match='AI evaluation is disabled'):
            action()
    assert not p.calls and not s.all('assessment_attempts') and not s.all('labels')


def test_planned_variation_constraints_and_assumption_validation():
    schema=scenario_generation.output_schema([],{'topic':'programming and algorithms','variation':'completed with understanding'})
    assert schema['properties']['progress']['anyOf'][0]['properties']['completed_units']['const']==1
    assert schema['properties']['control_results']['items']['properties']['recorded_assessment']['const']=='correct'
    missing=scenario_generation.output_schema(['control_results'],{'topic':'programming and algorithms','variation':'completed with understanding'})
    assert missing['properties']['control_results']=={'type':'null'}
    question={'text':'How did you complete all the planned work?','origin':bank_questions.ORIGIN,'conditions':{'present':['progress']}}
    with pytest.raises(ValueError,match='Completion wording'):
        bank_questions.parse(json.dumps(question))
    question['conditions']={'compare':[{'left':'progress.completed_units','op':'gte','right':'progress.planned_units'}]}
    assert bank_questions.parse(json.dumps(question))


def test_bank_diagnostics_excludes_inferred_assessments_and_rejected_rules():
    bank=[{'id':'fallback','question_id':'fallback','text':'Which approach would you like to reflect on?','conditions':{},'priority':0},
          {'id':'inferred','question_id':'inferred','text':'Which answer would you like to revisit?','conditions':{'contains':{'control_results':'incorrect'}},'priority':10},
          {'id':'rejected','question_id':'rejected','text':'What next?','conditions':{},'priority':100,'review_status':'rejected'}]
    scenarios=[{'id':'case','inputs':{'control_results':[{'ai_inferred_assessment':'incorrect'}]}}]
    diagnostic=bank_diagnostics.inspect(bank,scenarios)
    assert diagnostic['selections'][0]['selected_version_id']=='fallback'
    assert diagnostic['excluded_rejected_versions']==['rejected']
