#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def run(command, cwd):
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    output = completed.stdout + completed.stderr
    return completed.returncode, output


summaries = []
failures = []

for expected_path in sorted((ROOT / "scenarios").glob("*/expected.json")):
    scenario_dir = expected_path.parent
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    name = scenario_dir.name
    project = expected["project"]
    mode = expected.get("mode", "success")
    restore_args = expected.get("restoreArgs")
    if restore_args is None:
        restore_args = ["--locked-mode"]

    print(f"\n=== {name}: {expected['description']} ===", flush=True)
    code, output = run(["dotnet", "restore", project, *restore_args], scenario_dir)
    (scenario_dir / "restore.log").write_text(output, encoding="utf-8")
    print(output, flush=True)

    expected_codes = expected.get("expectedCodes", [])
    missing_codes = [item for item in expected_codes if item not in output]

    if mode == "failure":
        passed = code != 0 and not missing_codes
        detail = f"restore exit={code}; expected codes={expected_codes}"
    else:
        passed = code == 0 and not missing_codes
        detail = f"restore exit={code}"

        if passed:
            list_code, list_output = run(
                ["dotnet", "list", project, "package", "--include-transitive", "--no-restore"],
                scenario_dir,
            )
            print(list_output, flush=True)
            if list_code != 0:
                passed = False
                detail = f"package listing exit={list_code}"

        if passed:
            assets = scenario_dir / expected.get("assets", "obj/project.assets.json")
            verify_code, verify_output = run(
                [sys.executable, str(ROOT / "tools" / "verify_graph.py"), str(assets), str(expected_path)],
                scenario_dir,
            )
            print(verify_output, flush=True)
            if verify_code != 0:
                passed = False
                detail = "graph verification failed"

    summaries.append({"scenario": name, "mode": mode, "passed": passed, "detail": detail})
    if not passed:
        failures.append(f"{name}: {detail}; missing codes={missing_codes}")

(RESULTS / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")

print("\n=== Suite summary ===")
for item in summaries:
    print(f"{'PASS' if item['passed'] else 'FAIL'} {item['scenario']}: {item['detail']}")

if failures:
    print("\nFailures:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    raise SystemExit(1)
