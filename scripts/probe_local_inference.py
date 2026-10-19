"""Probe only the inspected loopback runtime; no datasets, installs or downloads."""
import argparse
import json
from pathlib import Path
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import URLError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=11435)
    parser.add_argument('--model', required=True, help='Explicit model tag to inspect; no cached-model default')
    parser.add_argument('--smoke', action='store_true', help='Explicitly run one READY-only local setup prompt, never dataset records')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('invalid local port')
    opener = build_opener(ProxyHandler({}))  # Never forward loopback through an environment proxy.
    base = f'http://127.0.0.1:{args.port}'
    def call(path, body=None):
        payload = None if body is None else json.dumps(body).encode('utf-8')
        request = Request(base + path, data=payload, headers={'Content-Type': 'application/json'})
        with opener.open(request, timeout=180) as response:
            return json.load(response)
    report = {'probe_kind': 'local_setup_only', 'external_processing': False, 'dataset_records_used': 0,
              'base_url': base, 'model_tag': args.model, 'generation_status': 'not_run',
              'model_reuse_terms': 'Not assessed by this metadata/setup probe; cache presence is not selection.'}
    try:
        report['runtime_version'] = call('/api/version')['version']
        models = call('/api/tags')['models']
        model = next((row for row in models if row['name'] == report['model_tag']), None)
        if model is None:
            raise ValueError('expected_local_model_missing')
        report['model_digest'] = model['digest']
        report['model_size_bytes'] = model['size']
        report['details'] = model.get('details', {})
        report['metadata_status'] = 'reachable_and_cached'
        if args.smoke:
            started = time.perf_counter()
            output = call('/api/generate', {'model': report['model_tag'], 'prompt': 'Reply with only the word READY.',
                          'stream': False, 'keep_alive': 0,
                          'options': {'temperature': 0, 'seed': 20261019, 'num_ctx': 2048, 'num_predict': 16}})
            report['setup_smoke_elapsed_seconds'] = round(time.perf_counter() - started, 3)
            report['setup_ready_response'] = output.get('response', '').strip() == 'READY'
            report['generation_status'] = 'completed' if output.get('done') else 'incomplete'
            report['comparison_result'] = 'None; a setup prompt is not a reflection-question experiment.'
    except (OSError, URLError, ValueError, StopIteration, KeyError):
        report['probe_status'] = 'not_completed'
        report['reason'] = 'Local runtime/model request failed; no raw server error or content logged.'
    else:
        report['probe_status'] = 'completed'
    filename = 'inference_probe.json' if args.smoke else 'inference_metadata_probe.json'
    destination = Path(__file__).resolve().parents[1] / 'reports' / filename
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['probe_status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
