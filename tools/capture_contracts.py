"""Capture candidate evidence; review before committing an expected contract."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from graph_contract import build_graph, load_json

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / sys.argv[1]
metadata = load_json(folder / 'scenario.json')
entry = folder / metadata['entry']
output = ROOT / 'drafts' / folder.relative_to(ROOT)
output.mkdir(parents=True, exist_ok=True)
result = subprocess.run(['dotnet', 'restore', str(entry), '--use-lock-file', '--force-evaluate'],
                        cwd=folder, text=True, capture_output=True, timeout=600)
print(result.stdout + result.stderr)
(output / 'restore.log').write_text(result.stdout + result.stderr, encoding='utf-8')
if result.returncode:
    raise SystemExit(result.returncode)
assets = folder / metadata.get('assets', 'obj/project.assets.json')
lock = folder / metadata.get('lock', 'packages.lock.json')
graph = build_graph(load_json(assets), load_json(lock), metadata['id'])
(output / 'expected').mkdir(exist_ok=True)
(output / 'expected/graph.json').write_text(json.dumps(graph, indent=2) + '\n', encoding='utf-8')
for path in folder.rglob('packages.lock.json'):
    destination = output / path.relative_to(folder)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
shutil.copy2(assets, output / 'project.assets.json')
listing = subprocess.run(['dotnet', 'list', str(entry), 'package', '--include-transitive', '--format', 'json'],
                         cwd=folder, text=True, capture_output=True, timeout=300)
(output / 'list.json').write_text(listing.stdout + listing.stderr, encoding='utf-8')
for context in metadata.get('additionalGraphs', []):
    result = subprocess.run(['dotnet', 'restore', str(folder / context['entry']), '--use-lock-file', '--force-evaluate'],
                            cwd=folder, text=True, capture_output=True, timeout=600)
    print(result.stdout + result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    graph = build_graph(load_json(folder / context['assets']), load_json(folder / context['lock']), metadata['id'])
    (output / context['expected']).write_text(json.dumps(graph, indent=2) + '\n', encoding='utf-8')
    for path in folder.rglob('packages.lock.json'):
        destination = output / path.relative_to(folder)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
