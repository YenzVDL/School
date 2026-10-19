"""Standard-library loopback-only Ollama transport. Never installs or pulls implicitly."""
import json
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler

QUESTION_SCHEMA = {'type': 'object', 'properties': {'question_text': {'type': 'string'}},
                   'required': ['question_text'], 'additionalProperties': False}


class LocalOllamaClient:
    def __init__(self, base_url='http://127.0.0.1:11435', timeout=180):
        url = urlsplit(base_url)
        if (url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password
                or url.path or url.query or url.fragment or not url.port or not 1024 <= url.port <= 65535):
            raise ValueError('explicit_ipv4_loopback_endpoint_required')
        self.base_url, self.timeout = base_url, timeout
        self.opener = build_opener(ProxyHandler({}))

    def call(self, path, body=None):
        if path not in {'/api/version', '/api/tags', '/api/show', '/api/chat'}:
            raise ValueError('unsupported_metadata_or_chat_path')
        data = None if body is None else json.dumps(body).encode('utf-8')
        request = Request(self.base_url + path, data=data, headers={'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=self.timeout) as response:
            return json.load(response)

    def model(self, tag):
        return next((row for row in self.call('/api/tags')['models'] if row['name'] == tag), None)

    def pull_explicitly_authorized(self, tag, progress):
        if tag != 'qwen3:8b':
            raise ValueError('only_the_explicitly_authorized_model_can_be_pulled')
        body = json.dumps({'model': tag, 'stream': True}).encode('utf-8')
        request = Request(self.base_url + '/api/pull', data=body, headers={'Content-Type': 'application/json'})
        success = False
        with self.opener.open(request, timeout=120) as response:
            for line in response:
                item = json.loads(line)
                if 'error' in item:
                    raise RuntimeError('model_pull_failed')
                progress(item)
                success = item.get('status') == 'success'
        if not success:
            raise RuntimeError('model_pull_not_completed')


def check_thinking_disabled(response):
    """Inspect the unmodified API response; never strip a thinking trace."""
    message = response.get('message', {})
    content = message.get('content')
    if not response.get('done') or not isinstance(content, str):
        raise ValueError('generation_not_completed')
    if message.get('thinking') or response.get('thinking'):
        raise ValueError('unexpected_thinking_trace')
    if '<think>' in content.casefold() or '</think>' in content.casefold():
        raise ValueError('unexpected_thinking_markup')
    return content


class LocalOllamaGenerator:
    """A future approved-record run must pass the engine's separate execution gate."""
    def __init__(self, config, client=None):
        self.config = config
        self.client = client or LocalOllamaClient(config['runtime']['base_url'], config['generation']['timeout_seconds'])

    def generate(self, request):
        model = self.config['model']
        if (request.model != model['selected'] or request.artifact_digest != model['artifact_digest']
                or request.think is not False):
            raise ValueError('shared_model_pin_or_thinking_control_mismatch')
        expected_options = {key:self.config['generation'][key] for key in
                            ('temperature','top_p','top_k','min_p','num_ctx','num_predict')}
        if (request.options != dict(expected_options, seed=request.options.get('seed'))
                or request.options.get('seed') not in self.config['generation']['seeds']
                or request.timeout_seconds != self.config['generation']['timeout_seconds']):
            raise ValueError('shared_generation_settings_mismatch')
        if self.client.call('/api/version')['version'] != self.config['runtime']['version']:
            raise ValueError('runtime_version_changed')
        installed = self.client.model(request.model)
        if installed is None or installed['digest'] != request.artifact_digest:
            raise ValueError('installed_model_digest_mismatch')
        response = self.client.call('/api/chat', {'model': request.model, 'stream': False, 'think': False,
            'format': QUESTION_SCHEMA, 'keep_alive': 0,
            'messages': [{'role': 'system', 'content': request.system}, {'role': 'user', 'content': request.payload_json}],
            'options': request.options})
        content = check_thinking_disabled(response)
        installed_after = self.client.model(request.model)
        if installed_after is None or installed_after['digest'] != request.artifact_digest:
            raise ValueError('model_digest_changed_during_generation')
        return content
