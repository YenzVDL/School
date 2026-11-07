"""Optional semantic integration uses provider doubles only, never live inference."""
import copy
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.semantic_evaluation import ANCHORS
from backend import script_evaluation
from .conftest import approved_inputs,wait_job


def collected(lab):
    s,r,p,jobs=lab
    *_,ds,bank=approved_inputs(r)
    job=jobs.create_experiment({'name':'Optional review','dataset_snapshot_id':ds['id'],'bank_snapshot_id':bank['id'],'methods':['fixed']})
    wait_job(s,job['id'])
    return job,s.all('outputs')[0]


def payload(output,enabled=True):
    return {'enabled':enabled,'model':'test-fixture-model','output_id':output['id'],'output_version':output['version']}


def response(ratings):
    return {'text':json.dumps(ratings),'runtime':{'done_reason':'stop'},'effective_settings':{'think':False}}


def ratings():
    return {k:{'value':3,'evidence':'Available learning activity','explanation':'Test fixture rating only'} for k in ANCHORS}


def test_semantic_disabled_by_default_no_provider_call(lab):
    s,r,p,jobs=lab
    job,output=collected(lab)
    with TestClient(create_app(s,p)) as client:
        assert client.post('/api/semantic-evaluations',json=payload(output,False)).status_code==422
        assert client.get('/api/jobs/'+job['id']+'/semantic-evaluations').json()==[]
    assert not p.calls and not s.all('semantic_assessments')


def test_opt_in_estimates_preserve_fixed_metrics_and_method_blind_request(lab):
    s,r,p,jobs=lab
    job,output=collected(lab)
    s.patch('outputs',output['id'],method='SECRET_METHOD',model='SECRET_GENERATOR',trace={'conditions':{'secret':'not evidence'}},research_labels={'secret':'not evidence'})
    before=copy.deepcopy(s.all('outputs'))
    fixed=script_evaluation.save(s,job['id'])
    observed=[]
    def generate(model,system,prompt,settings,cancel,**kwargs):
        observed.append(json.loads(prompt))
        assert set(observed[-1])=={'scenario_inputs','reflection_question','rating_anchors_1_to_4'}
        assert 'SECRET_' not in prompt and 'research_labels' not in prompt and 'conditions' not in prompt
        assert settings['_model_digest']=='fixture'
        return response(ratings())
    p.generate=generate
    with TestClient(create_app(s,p)) as client:
        record=client.post('/api/semantic-evaluations',json=payload(output)).json()
        assert record['status']=='completed' and record['model_digest']=='fixture'
        assert record['source']=='local_ai_assisted' and record['rubric_version']=='semantic-rubric-v1'
        assert record['sampling_settings']['temperature']==0
        assert len(record['ratings'])==6
        export=client.get('/api/jobs/'+job['id']+'/export').json()
        assert export['semantic_evaluations']==[record] and export['script_evaluations']==[fixed]
        assert export['metrics']['semantic_review_coverage']['ai_estimated_outputs']==1
    assert s.all('outputs')==before and script_evaluation.save(s,job['id'])==fixed
    assert not s.all('labels')
    with pytest.raises(ValueError,match='immutable'):
        s.patch('semantic_assessments',record['id'],ratings={})


@pytest.mark.parametrize('invalid',[{}, {**ratings(),'clarity':{'value':5,'evidence':'x','explanation':'x'}}, {**ratings(),'clarity':{'value':True,'evidence':'x','explanation':'x'}}])
def test_malformed_semantic_estimates_never_default_to_positive(lab,invalid):
    s,r,p,jobs=lab
    job,output=collected(lab)
    p.generate=lambda *a,**kw:response(invalid)
    with TestClient(create_app(s,p)) as client:
        record=client.post('/api/semantic-evaluations',json=payload(output)).json()
    assert record['status']=='failed' and 'ratings' not in record
    assert s.all('semantic_assessments')==[record] and not s.all('labels')


def test_model_digest_drift_discards_estimates(lab):
    s,r,p,jobs=lab
    job,output=collected(lab)
    def drift(*a,**kw):
        p.models=lambda:[{'name':'test-fixture-model','digest':'changed','details':{}}]
        return response(ratings())
    p.generate=drift
    with TestClient(create_app(s,p)) as client:
        record=client.post('/api/semantic-evaluations',json=payload(output)).json()
    assert record['status']=='failed' and 'digest changed' in record['error'] and 'ratings' not in record
