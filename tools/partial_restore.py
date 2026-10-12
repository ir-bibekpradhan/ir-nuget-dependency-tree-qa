"""Inspect per-project diagnostics without treating failed assets as successful truth."""
import hashlib
import json
import shutil
from pathlib import Path
from graph_contract import split_target


def inspect_partial(folder, output, contracts):
    states = []
    evidence = output / 'partial-evidence'
    evidence.mkdir(exist_ok=True)
    for contract in contracts:
        path = folder / contract['assets']
        assets = json.loads(path.read_text(encoding='utf-8'))
        codes = {log.get('code') for log in assets.get('logs', []) if log.get('level', '').lower() == 'error'}
        expected = set(contract['errorCodes'])
        if codes != expected:
            raise ValueError(f"{contract['project']}: expected error codes {expected}, got {codes}")
        validated_edges = []
        for rule in contract.get('resolvedEdges', []):
            target = next((value for name, value in assets['targets'].items()
                           if split_target(name) == (rule['framework'], None)), None)
            if target is None:
                raise ValueError('Missing partial framework ' + rule['framework'])
            parent_key = rule['from'].replace('@', '/')
            child_key = rule['to'].replace('@', '/')
            if parent_key not in target or child_key not in target or child_key.rsplit('/', 1)[0] not in target[parent_key].get('dependencies', {}):
                raise ValueError('Missing successful-project resolved edge ' + str(rule))
            validated_edges.append(rule)
        for project in contract.get('projectReferences', []):
            for name, target in assets['targets'].items():
                if not any(key.rsplit('/', 1)[0] == project and value.get('type') == 'project' for key, value in target.items()):
                    raise ValueError(f'{name}: missing local project node {project}')
        project_evidence = evidence / contract['project']
        project_evidence.mkdir(exist_ok=True)
        shutil.copy2(path, project_evidence / 'project.assets.json')
        states.append({'project': contract['project'], 'restoreSuccess': not codes, 'errorCodes': sorted(codes),
                       'assetsSha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'jsonValid': True,
                       'validatedResolvedEdges': validated_edges, 'projectReferences': contract.get('projectReferences', [])})
    return states
