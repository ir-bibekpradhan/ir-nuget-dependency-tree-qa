#!/usr/bin/env python3
import json
import sys
from pathlib import Path

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

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(ids)} scenario contracts.")
