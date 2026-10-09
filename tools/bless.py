#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from graph_contract import build_graph, load_json

parser = argparse.ArgumentParser()
parser.add_argument("--scenario", required=True)
parser.add_argument("--assets", required=True)
parser.add_argument("--lock", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

graph = build_graph(load_json(args.assets), load_json(args.lock), args.scenario)
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
print(f"Drafted {args.output}; human review is required before commit.")
