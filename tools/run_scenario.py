#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import shutil
import time
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument("scenario_dir")
args = parser.parse_args()

scenario_dir = (ROOT / args.scenario_dir).resolve()
metadata_path = scenario_dir / "scenario.json"
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
scenario_id = metadata["id"]
entry = scenario_dir / metadata["entry"]
assets = scenario_dir / metadata.get("assets", "obj/project.assets.json")
lock = scenario_dir / metadata.get("lock", "packages.lock.json")
expected = scenario_dir / "expected" / "graph.json"
output = ROOT / "out" / scenario_id
output.mkdir(parents=True, exist_ok=True)
(output / "summary.md").write_text(f"# {scenario_id} result\n\n- Status: FAIL (verification did not finish)\n- IR comparison: pending export\n", encoding="utf-8")


def execute(command, cwd=scenario_dir):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=600)
    combined = result.stdout + result.stderr
    print(combined, flush=True)
    return result.returncode, combined


restore = metadata["restore"]
restore_args = list(restore.get("arguments", []))
if restore["mode"] == "locked":
    restore_args.append("--locked-mode")
elif restore["mode"] == "generate":
    restore_args.extend(["--use-lock-file", "--force-evaluate"])
elif restore["mode"] == "offline":
    if metadata.get("primeCache"):
        prime_code, prime_log = execute(["dotnet", "restore", str(entry), "--locked-mode"])
        (output / "prime.log").write_text(prime_log, encoding="utf-8")
        if prime_code != 0:
            raise SystemExit("Cache priming failed")
    empty_feed = output / "empty-feed"
    empty_feed.mkdir(exist_ok=True)
    restore_args.extend(["--locked-mode", "--source", str(empty_feed), "-p:NuGetAudit=false"])

started = time.perf_counter()
code, restore_output = execute(["dotnet", "restore", str(entry), *restore_args])
(output / "metrics.json").write_text(json.dumps({"restoreSeconds": time.perf_counter() - started}, indent=2) + "\n", encoding="utf-8")
(output / "restore.log").write_text(restore_output, encoding="utf-8")
expected_codes = restore.get("expectedCodes", [])
missing_codes = [item for item in expected_codes if item not in restore_output]

if not restore["expectSuccess"]:
    passed = code != 0 and not missing_codes
    result = {
        "scenario": scenario_id,
        "expectedRestoreSuccess": False,
        "restoreExitCode": code,
        "expectedCodes": expected_codes,
        "missingCodes": missing_codes,
        "passed": passed,
    }
    (output / "diff.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (output / "summary.md").write_text(
        f"# {scenario_id} result\n\n- Expected restore failure: {'PASS' if passed else 'FAIL'}\n",
        encoding="utf-8",
    )
    if not passed:
        raise SystemExit(1)
    raise SystemExit(0)

if code != 0 or missing_codes:
    raise SystemExit(f"{scenario_id}: restore failed or expected warnings were absent: {missing_codes}")

list_code, list_output = execute([
    "dotnet", "list", str(entry), "package", "--include-transitive", "--format", "json"
])
(output / "list.json").write_text(list_output, encoding="utf-8")
if list_code != 0:
    raise SystemExit(f"{scenario_id}: dotnet list package failed")

if metadata.get("vulnerabilityPackages"):
    vuln_code, vuln_output = execute([
        "dotnet", "list", str(entry), "package", "--vulnerable", "--include-transitive", "--format", "json"
    ])
    (output / "vulnerabilities.json").write_text(vuln_output, encoding="utf-8")
    if vuln_code != 0:
        raise SystemExit(f"{scenario_id}: vulnerability query failed")
    vuln_data = json.loads(vuln_output)
    affected = {package['id'].lower() for project in vuln_data.get('projects', [])
                for framework in project.get('frameworks', [])
                for field in ('topLevelPackages', 'transitivePackages')
                for package in framework.get(field, []) if package.get('vulnerabilities')}
    missing = [item for item in metadata["vulnerabilityPackages"] if item.lower() not in affected]
    if missing:
        raise SystemExit(f"{scenario_id}: expected vulnerable packages missing: {missing}")

ir_argument = []
shutil.copy2(assets, output / "project.assets.json")
shutil.copy2(lock, output / "packages.lock.json")
from graph_contract import build_graph, canonical, load_json


def graph_hash():
    value = canonical(build_graph(load_json(assets), load_json(lock), scenario_id))
    stable = [(key, {field: sorted(map(str, items)) for field, items in target.items()})
              for key, target in sorted(value.items())]
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


hashes = [graph_hash()]
for repeat in range(1, metadata.get('repeats', 1)):
    assets.unlink()  # Only the generated assets file for this isolated fixture.
    repeat_code, repeat_log = execute(["dotnet", "restore", str(entry), *restore_args, "--force"])
    (output / f"repeat-{repeat + 1}.log").write_text(repeat_log, encoding="utf-8")
    if repeat_code != 0:
        raise SystemExit("Repeated restore failed")
    hashes.append(graph_hash())
(output / "hashes.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
if len(set(hashes)) != 1:
    raise SystemExit("Graph changed across repeated restores")
ir_path = os.environ.get("IR_GRAPH_PATH", "").strip()
if ir_path:
    normalized_ir = output / "ir.json"
    adapter_code, _ = execute([
        sys.executable, str(ROOT / "tools" / "ir_export_adapter.py"),
        "--input", ir_path, "--output", str(normalized_ir),
    ])
    if adapter_code != 0:
        raise SystemExit(f"{scenario_id}: IR export adapter failed")
    ir_argument = ["--ir", str(normalized_ir)]

verify_command = [
    sys.executable, str(ROOT / "tools" / "verify_contract.py"),
    "--scenario", scenario_id,
    "--assets", str(assets),
    "--lock", str(lock),
    "--expected", str(expected),
    "--actual", str(output / "nuget.json"),
    "--diff", str(output / "diff.json"),
    "--summary", str(output / "summary.md"),
    *ir_argument,
]
verify_code, _ = execute(verify_command)
if verify_code != 0:
    raise SystemExit(f"{scenario_id}: graph contract comparison failed")
