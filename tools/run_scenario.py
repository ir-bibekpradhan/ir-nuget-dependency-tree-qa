#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
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


def execute(command, cwd=scenario_dir):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
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
    restore_args.extend(["--locked-mode", "--no-cache", "--ignore-failed-sources"])

code, restore_output = execute(["dotnet", "restore", str(entry), *restore_args])
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
    "dotnet", "list", str(entry), "package", "--include-transitive", "--format", "json", "--no-restore"
])
(output / "list.json").write_text(list_output, encoding="utf-8")
if list_code != 0:
    raise SystemExit(f"{scenario_id}: dotnet list package failed")

if metadata.get("vulnerabilityPackages"):
    vuln_code, vuln_output = execute([
        "dotnet", "list", str(entry), "package", "--vulnerable", "--include-transitive", "--format", "json", "--no-restore"
    ])
    (output / "vulnerabilities.json").write_text(vuln_output, encoding="utf-8")
    if vuln_code != 0:
        raise SystemExit(f"{scenario_id}: vulnerability query failed")
    lowered = vuln_output.lower()
    missing = [item for item in metadata["vulnerabilityPackages"] if item.lower() not in lowered]
    if missing:
        raise SystemExit(f"{scenario_id}: expected vulnerable packages missing: {missing}")

ir_argument = []
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
