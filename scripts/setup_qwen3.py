"""Explicit qwen3:8b acquisition and generic setup only; never reads research records."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ollama_local import LocalOllamaClient, QUESTION_SCHEMA, check_thinking_disabled

ROOT = Path(__file__).resolve().parents[1]
TAG = 'qwen3:8b'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hardware():
    def powershell(command):
        result = subprocess.run(['powershell', '-NoProfile', '-Command', command], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    cpu = powershell('Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json')
    memory = powershell('Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json')
    smi = Path(os.environ['WINDIR']) / 'System32/nvidia-smi.exe'
    output = subprocess.run([str(smi), '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'],
                            capture_output=True, text=True, check=True).stdout.strip()
    name, size, driver = [part.strip() for part in output.split(',')]
    return dict(cpu=cpu['Name'].strip(), physical_cores=cpu['NumberOfCores'], logical_processors=cpu['NumberOfLogicalProcessors'],
                ram_bytes=memory['TotalPhysicalMemory'], gpu=name, gpu_memory_mib=int(size.split()[0]), nvidia_driver=driver)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pull-if-needed', action='store_true', help='Explicit user-authorized qwen3:8b download')
    parser.add_argument('--smoke', action='store_true', help='Two fixed generic JSON probes, no dataset records')
    parser.add_argument('--check', action='store_true', help='Metadata/configuration only; no download or generation')
    args = parser.parse_args()
    if args.check and (args.smoke or args.pull_if_needed):
        parser.error('--check cannot download or generate')
    client = LocalOllamaClient()
    exe = Path(os.environ['LOCALAPPDATA']) / 'Programs/AnythingLLM/resources/ollama/llm.exe'
    before = digest(exe.read_bytes())
    version = client.call('/api/version')['version']
    parsed = tuple(int(part) for part in re.match(r'^(\d+)\.(\d+)\.(\d+)', version).groups())
    report = dict(model_tag=TAG, checked_at_utc=datetime.now(timezone.utc).isoformat(), runtime_version=version,
                  bundled_executable=str(exe), executable_sha256_before=before, hardware=hardware(),
                  research_records_used=0, paid_apis_used=False, research_data_uploaded=False,
                  runtime_upgrade_performed=False, thinking_request_value=False, model_pulled=False)
    if parsed < (0, 9, 0):
        report.update(status='blocked', compatibility_blocker='Installed Ollama predates supported think API; no upgrade performed.')
    else:
        installed = client.model(TAG)
        if installed is None and args.pull_if_needed:
            print('Pulling only qwen3:8b through the existing local Ollama server.', flush=True)
            last = {'status': None, 'gib': -1, 'time': 0}
            def progress(item):
                now, status = time.monotonic(), item.get('status','')
                gib = item.get('completed',0) // (1024**3)
                if status != last['status'] or gib > last['gib'] or now-last['time'] >= 20:
                    print(json.dumps({'status': status, 'completed_bytes': item.get('completed'), 'total_bytes': item.get('total')}), flush=True)
                    last.update(status=status,gib=gib,time=now)
            client.pull_explicitly_authorized(TAG, progress)
            report['model_pulled'] = True
            installed = client.model(TAG)
        if installed is None:
            report.update(status='blocked', compatibility_blocker='qwen3:8b is not cached. Explicit --pull-if-needed is required.')
        else:
            shown = client.call('/api/show', {'model': TAG})
            template = shown.get('template','')
            report.update(status='metadata_ready', model_digest=installed['digest'], model_size_bytes=installed['size'],
                          quantization=installed.get('details',{}).get('quantization_level'),
                          parameter_size=installed.get('details',{}).get('parameter_size'),
                          capabilities=shown.get('capabilities',[]), template_sha256=digest(template.encode('utf-8')),
                          template_has_thinking_control='Thinking' in template or 'Think' in template,
                          license_sha256=digest(shown.get('license','').encode('utf-8')))
            config_path = ROOT / 'configs/experiment_v0_2.json'
            config = json.loads(config_path.read_text(encoding='utf-8'))
            if not args.check:
                config['model'].update(selected=TAG,artifact_digest=installed['digest'],recommended_candidate=None,
                                       selection_status='user_selected_setup_pending',same_artifact_for_rag_and_direct=True)
                config['generator'] = {'backend':'ollama_local','integration':'LocalOllamaGenerator; experiment execution remains disabled'}
                config['experiments_enabled'] = False
                config['generation'].update(think=False,temperature=0.7,top_p=0.8,top_k=20,min_p=0)
                config['runtime'] = dict(provider='AnythingLLM_bundled_Ollama',version=version,base_url=client.base_url,
                    executable=str(exe),executable_sha256=before,quantization=report['quantization'],
                    model_size_bytes=installed['size'],parameter_size=report['parameter_size'],
                    template_sha256=report['template_sha256'],license_sha256=report['license_sha256'])
                config['hardware'] = report['hardware']
            if args.smoke:
                options = {key:config['generation'][key] for key in ('temperature','top_p','top_k','min_p','num_ctx','num_predict')}
                options['seed'] = config['generation']['seeds'][0]
                probes = []
                for suffix in ('', ' /think'):
                    request = {'model':TAG,'stream':False,'think':False,'format':QUESTION_SCHEMA,'keep_alive':0,
                        'messages':[{'role':'system','content':'This is a generic software setup test. Return exactly one JSON object with only question_text.'},
                                    {'role':'user','content':'Return exactly {"question_text":"Is setup ready?"}.'+suffix}], 'options':options}
                    started = time.perf_counter()
                    response = client.call('/api/chat',request)
                    elapsed = time.perf_counter()-started
                    content = check_thinking_disabled(response)
                    output = json.loads(content)
                    assert output == {'question_text':'Is setup ready?'}
                    assert client.model(TAG)['digest'] == installed['digest']
                    probes.append(dict(probe='generic_json' if not suffix else 'generic_json_with_soft_think_hint',
                        request=request,response=response,observed_wall_seconds=round(elapsed,3),
                        response_format_valid=True,thinking_field_nonempty=False,reasoning_text_removed=False))
                report.update(status='setup_verified',probes=probes,
                              conclusion='API think:false accepted; raw responses contain no thinking trace; format verified. No reflection-quality evidence.')
                config['model']['selection_status']='user_selected_generic_setup_verified_not_approach_comparison'
            if args.check:
                assert config['model']['selected']==TAG and config['model']['artifact_digest']==installed['digest']
                assert config['generation']['think'] is False and config['experiments_enabled'] is False
                assert config['runtime']['version']==version and config['runtime']['quantization']==report['quantization']
                report['configuration_matches'] = True
            else:
                config_path.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    report['executable_sha256_after'] = digest(exe.read_bytes())
    assert report['executable_sha256_after']==before
    filename = ('qwen3_8b_metadata_check.json' if args.check else
                'qwen3_8b_acquisition.json' if args.pull_if_needed and not args.smoke else 'qwen3_8b_setup.json')
    destination = ROOT / 'reports' / filename
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key!='probes'},indent=2))
    return 1 if report['status']=='blocked' else 0


if __name__=='__main__':
    raise SystemExit(main())
