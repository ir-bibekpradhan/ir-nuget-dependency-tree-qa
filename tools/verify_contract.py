#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from graph_contract import build_graph, compare, load_json

parser = argparse.ArgumentParser()
parser.add_argument("--scenario", required=True)
parser.add_argument("--assets", required=True)
parser.add_argument("--lock", required=True)
parser.add_argument("--expected", required=True)
parser.add_argument("--actual", required=True)
parser.add_argument("--diff", required=True)
parser.add_argument("--summary", required=True)
parser.add_argument("--ir")
args = parser.parse_args()

actual = build_graph(load_json(args.assets), load_json(args.lock), args.scenario)
Path(args.actual).write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
expected = load_json(args.expected)
passed, nuget_diff = compare(expected, actual)

result = {"scenario": args.scenario, "nugetMatchesExpected": passed, "nugetDiff": nuget_diff}
if args.ir:
    ir = load_json(args.ir)
    ir_passed, ir_diff = compare(expected, ir, compare_requested=False)
    result.update({"irMatchesExpected": ir_passed, "irDiff": ir_diff})
    passed = passed and ir_passed

Path(args.diff).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
summary = f"# {args.scenario} result\n\n- NuGet vs expected: {'PASS' if result['nugetMatchesExpected'] else 'FAIL'}\n"
if "irMatchesExpected" in result:
    summary += f"- IR vs expected: {'PASS' if result['irMatchesExpected'] else 'FAIL'}\n"
else:
    result['irStatus'] = 'pending-export'
    summary += "- IR comparison: PENDING (no graph export supplied)\n"
Path(args.diff).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
Path(args.summary).write_text(summary, encoding="utf-8")
print(summary)
if not passed:
    raise SystemExit(1)
