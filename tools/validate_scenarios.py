#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from graph_contract import load_json, structural_errors

ROOT = Path(__file__).resolve().parents[1]
errors = []
ids = set()

for path in sorted((ROOT / "scenarios").glob("*/scenario.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ["id", "name", "phase", "entry", "restore", "deterministic", "checks"]
    for field in required:
        if field not in data:
            errors.append(f"{path}: missing {field}")
    if data.get("id") in ids:
        errors.append(f"{path}: duplicate id {data.get('id')}")
    ids.add(data.get("id"))
    if not (path.parent / data.get("entry", "")).exists():
        errors.append(f"{path}: entry does not exist")
    if data.get("restore", {}).get("expectSuccess") and not data.get('capture') and not (path.parent / "expected" / "graph.json").exists():
        errors.append(f"{path}: successful scenario lacks expected/graph.json")
    if not (path.parent / "README.md").exists():
        errors.append(f"{path}: missing README.md")
    if data.get('restore', {}).get('expectSuccess') and not data.get('capture'):
        expected_paths = ['expected/graph.json'] + [context['expected'] for context in data.get('additionalGraphs', [])]
        if data.get('afterRestore'):
            expected_paths.append(data['afterRestore']['expected'])
        for expected_path in expected_paths:
            if (path.parent / expected_path).exists():
                graph = load_json(path.parent / expected_path)
                if graph.get('schemaVersion') != 1:
                    errors.append(f'{path}: unsupported expected graph schema')
                errors.extend(f'{path}: {item}' for item in structural_errors(graph))
            else:
                errors.append(f'{path}: missing expected graph {expected_path}')
        if data['restore']['mode'] in ('locked', 'offline'):
            lock_paths = [data.get('lock', 'packages.lock.json')] + [context['lock'] for context in data.get('additionalGraphs', [])]
            for lock_path in lock_paths:
                if not (path.parent / lock_path).exists():
                    errors.append(f'{path}: missing lock {lock_path}')

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(ids)} scenario contracts.")
