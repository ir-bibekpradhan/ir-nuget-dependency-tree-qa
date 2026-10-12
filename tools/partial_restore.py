"""Inspect per-project diagnostics without treating failed assets as successful truth."""
import hashlib
import json
import shutil
from pathlib import Path


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
        project_evidence = evidence / contract['project']
        project_evidence.mkdir(exist_ok=True)
        shutil.copy2(path, project_evidence / 'project.assets.json')
        states.append({'project': contract['project'], 'restoreSuccess': not codes, 'errorCodes': sorted(codes),
                       'assetsSha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'jsonValid': True})
    return states
