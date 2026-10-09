#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["deterministic", "nightly", "all", "capture"], default="all")
args = parser.parse_args()

items = []
for path in sorted((ROOT / "scenarios").glob("*/scenario.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get('capture') and args.mode != 'capture':
        continue
    include = (
        args.mode == "all"
        or (args.mode == "capture" and data.get('capture', False))
        or (args.mode == "deterministic" and data.get("deterministic", False))
        or (args.mode == "nightly" and data.get("nightly", not data.get("deterministic", True)))
    )
    if include:
        items.append({
            "id": data["id"],
            "name": data["name"],
            "path": path.parent.relative_to(ROOT).as_posix(),
            "os": data.get("os", "ubuntu-latest"),
        })

print(json.dumps({"scenario": items}, separators=(",", ":")))
