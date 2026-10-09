#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Normalize an IR graph export for contract comparison")
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

data = json.loads(Path(args.input).read_text(encoding="utf-8"))
if data.get("schemaVersion") == 1 and isinstance(data.get("targets"), list):
    normalized = data
else:
    raise SystemExit(
        "Unsupported IR export format. Provide the normalized schema or extend this adapter once the IR API/SBOM export is confirmed."
    )

Path(args.output).write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
