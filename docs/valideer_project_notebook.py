"""Execute the read-only walkthrough with the project Python and a local kernel."""
import hashlib
import json
import os
import site
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
notebook_path = ROOT / 'docs/Zelfregiekompas_projectopbouw_en_metrics.ipynb'
protected = sorted((ROOT / 'docs/final-test-20261030').glob('*.json'))
protected += sorted((ROOT / 'docs/fixed-metrics-v3').glob('*.json'))

def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}

before = hashes()
kernel_root = ROOT / 'tmp/notebook-validation/kernels'
kernel_dir = kernel_root / 'zelfregiekompas-project'
kernel_dir.mkdir(parents=True, exist_ok=True)
executable = ROOT / '.venv/Scripts/python.exe'
kernel = {
    'argv': [str(executable), '-m', 'ipykernel_launcher',
             '--HistoryManager.enabled=False', '-f', '{connection_file}'],
    'display_name': 'Project validation', 'language': 'python',
    'env': {'IPYTHONDIR': str(ROOT / 'tmp/notebook-validation/ipython'),
            'PYTHONPATH': os.pathsep.join([
        str(ROOT / '.venv/Lib/site-packages'),
        site.getusersitepackages(),
        str(Path(sys.executable).parent / 'Lib/site-packages'),
    ])},
}
(kernel_dir / 'kernel.json').write_text(json.dumps(kernel), encoding='utf-8')
notebook = nbformat.read(notebook_path, as_version=4)
nbformat.validate(notebook)
for i, cell in enumerate(notebook.cells):
    if cell.cell_type == 'code':
        compile(cell.source, f'notebook-cell-{i}', 'exec')
manager = KernelManager(
    kernel_name='zelfregiekompas-project',
    kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernel_root)]),
)
client = NotebookClient(notebook, km=manager, timeout=90,
                        resources={'metadata': {'path': str(ROOT)}})
client.execute()
assert before == hashes(), 'An archived research artifact changed during execution'
errors = [o for c in notebook.cells if c.cell_type == 'code'
          for o in c.outputs if o.output_type == 'error']
assert not errors
nbformat.validate(notebook)
nbformat.write(notebook, notebook_path)
validation = {
    'notebook': str(notebook_path.relative_to(ROOT)),
    'execution': 'Jupyter kernel via nbclient',
    'executable': str(executable),
    'cells': len(notebook.cells),
    'executed_code_cells': sum(c.cell_type == 'code' and c.execution_count is not None for c in notebook.cells),
    'errors': len(errors),
    'archived_json_files_unchanged': len(before),
    'policy': 'No model calls, new experiments or database writes; archived JSON hashes checked before and after.',
}
(ROOT / 'docs/project_notebook_validatie.json').write_text(
    json.dumps(validation, indent=2) + '\n', encoding='utf-8')
print(json.dumps(validation, indent=2))
