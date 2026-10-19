"""Loopback transport tests use only a fake client; no model or HTTP calls."""
import copy
import json
from pathlib import Path
import unittest
import approaches as a
from ollama_local import LocalOllamaClient, LocalOllamaGenerator, QUESTION_SCHEMA, check_thinking_disabled


class FakeClient:
    def __init__(self, config):
        self.config, self.calls = config, []
        self.response = {'done': True, 'message': {'content': '{"question_text":"Is fixture ready?"}'}}
        self.drift = False

    def model(self, tag):
        return {'digest': '0'*64 if self.drift and any(path=='/api/chat' for path,_ in self.calls)
                else self.config['model']['artifact_digest']}

    def call(self, path, body=None):
        self.calls.append((path,body))
        if path=='/api/version':
            return {'version':self.config['runtime']['version']}
        if path=='/api/chat':
            return copy.deepcopy(self.response)
        raise AssertionError('Unexpected fake-client path')


class LocalTransportTests(unittest.TestCase):
    def setUp(self):
        self.config=a.load_config()
        self.client=FakeClient(self.config)
        self.backend=LocalOllamaGenerator(self.config,self.client)

    def request(self, think=False, options=None):
        settings=self.config['generation']
        shared={key:settings[key] for key in ('temperature','top_p','top_k','min_p','num_ctx','num_predict')}
        return a.GenerationRequest(self.config['model']['selected'],self.config['model']['artifact_digest'],
            'Unit fixture only.','{"fixture":"no research record"}',
            options or dict(shared,seed=settings['seeds'][0]),settings['timeout_seconds'],think)

    def test_native_think_false_and_schema_are_sent_not_postprocessed(self):
        raw=self.backend.generate(self.request())
        self.assertEqual(raw,self.client.response['message']['content'])
        body=next(body for path,body in self.client.calls if path=='/api/chat')
        self.assertIs(body['think'],False)
        self.assertNotIn('think',body['options'])
        self.assertEqual(body['format'],QUESTION_SCHEMA)
        self.assertEqual(body['model'],self.config['model']['selected'])
        self.assertIs(body['stream'],False)

    def test_thinking_trace_or_markup_is_rejected_never_stripped(self):
        for response in [{'done':True,'message':{'content':'{"question_text":"Ready?"}','thinking':'fixture trace'}},
                         {'done':True,'message':{'content':'<think>fixture</think>{"question_text":"Ready?"}'}},
                         {'done':False,'message':{'content':'{"question_text":"Ready?"}'}}]:
            with self.assertRaises(ValueError):
                check_thinking_disabled(response)
        with self.assertRaises(ValueError):
            self.backend.generate(self.request(think=True))
        self.assertEqual(self.client.calls,[])

    def test_model_drift_or_setting_drift_blocks(self):
        self.client.drift=True
        with self.assertRaises(ValueError):
            self.backend.generate(self.request())
        self.client.calls=[]
        with self.assertRaises(ValueError):
            self.backend.generate(self.request(options={'temperature':99,'seed':20261019}))
        self.assertEqual(self.client.calls,[])

    def test_remote_endpoints_and_implicit_other_pulls_are_forbidden(self):
        for endpoint in ['https://example.invalid:443','http://0.0.0.0:11435','http://127.0.0.1:11435/path',
                         'http://user:secret@127.0.0.1:11435','http://localhost:11435']:
            with self.assertRaises(ValueError):
                LocalOllamaClient(endpoint)
        client=LocalOllamaClient()
        with self.assertRaises(ValueError):
            client.pull_explicitly_authorized('another-model',lambda item:None)
        with self.assertRaises(ValueError):
            client.call('/api/pull',{})

    def test_pending_material_blocks_before_real_adapter_can_call(self):
        material=a.Material(Path('.'),'unit_fixture',{}, {'S01'}, {}, [])
        engine=a.ApproachEngine(material,self.config,self.backend)
        for method in ('fixed','rag','direct'):
            self.assertEqual(engine.run('S01',method)['status'],'scenario_approval_required')
        self.assertEqual(self.client.calls,[])


if __name__=='__main__':
    unittest.main()
