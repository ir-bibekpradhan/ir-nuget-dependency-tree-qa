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
os.environ.setdefault('NUGET_PACKAGES', str(ROOT / '.nuget' / ('packages-' + scenario_id)))
os.environ.setdefault('NUGET_HTTP_CACHE_PATH', str(ROOT / '.nuget' / ('http-' + scenario_id)))
(output / "summary.md").write_text(f"# {scenario_id} result\n\n- Status: FAIL (verification did not finish)\n- IR comparison: pending export\n", encoding="utf-8")


def execute(command, cwd=scenario_dir):
    result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=600)
    combined = (result.stdout + result.stderr).decode('utf-8', errors='replace')
    print(combined, flush=True)
    return result.returncode, combined


restore = metadata["restore"]
if metadata.get('restoreOutputControls'):
    from collector_fixtures import install_wrapper
    control_directory, control_binary = install_wrapper(scenario_dir, shutil.which('dotnet'), restore_controls=True)
    if os.environ.get('GITHUB_PATH'):
        with open(os.environ['GITHUB_PATH'], 'a', encoding='utf-8') as path_file:
            path_file.write(str(control_binary) + '\n')
if metadata.get('localFeed'):
    from local_feed import prepare
    prepare(scenario_dir)
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
    project_states = []
    if metadata.get('expectedProjectResults'):
        from partial_restore import inspect_partial
        try:
            project_states = inspect_partial(scenario_dir, output, metadata['expectedProjectResults'])
        except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
            passed = False
            (output / 'partial-error.txt').write_text(str(error), encoding='utf-8')
    result = {
        "scenario": scenario_id,
        "expectedRestoreSuccess": False,
        "restoreExitCode": code,
        "expectedCodes": expected_codes,
        "missingCodes": missing_codes,
        "passed": passed,
        "projectStates": project_states,
        "irStatus": "manual: failed or partial restore, no complete successful graph",
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

if metadata.get("vulnerabilityPackages") or metadata.get('absentAdvisories'):
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
    missing = [item for item in metadata.get("vulnerabilityPackages", []) if item.lower() not in affected]
    if missing:
        raise SystemExit(f"{scenario_id}: expected vulnerable packages missing: {missing}")
    if any(advisory.lower() in vuln_output.lower() for advisory in metadata.get('absentAdvisories', [])):
        raise SystemExit('An advisory for the old version was attached to the fixed-version context')

ir_argument = []
shutil.copy2(assets, output / "project.assets.json")
shutil.copy2(lock, output / "packages.lock.json")
from graph_contract import build_graph, canonical, load_json, check_listing, has_real_assets
listing_errors = check_listing(build_graph(load_json(assets), load_json(lock), scenario_id), json.loads(list_output))
if listing_errors:
    raise SystemExit('; '.join(listing_errors))
if metadata.get('floating'):
    import urllib.request
    from graph_contract import normalize_version
    rule = metadata['floating']
    with urllib.request.urlopen('https://api.nuget.org/v3-flatcontainer/' + rule['package'].lower() + '/index.json', timeout=60) as response:
        published = json.load(response)['versions']
    candidates = [version for version in published if '-' not in version and version.startswith(rule['prefix'])]
    highest = max(candidates, key=lambda version: tuple(int(part) for part in normalize_version(version).split('.')))
    draft = load_json(expected)
    for target in draft['targets']:
        node = next(node for node in target['nodes'] if node['type'] == 'package' and node['id'].split('@')[0].lower() == rule['package'].lower())
        old_ref = node['id']
        new_ref = rule['package'] + '@' + highest
        node['id'] = new_ref
        for edge in target['edges']:
            for field in ('from', 'to'):
                if edge[field] == old_ref:
                    edge[field] = new_ref
        target['paths'] = {(new_ref if key == old_ref else key): [[new_ref if part == old_ref else part for part in path] for path in values]
                           for key, values in target['paths'].items()}
    expected = output / 'floating-expected.json'
    expected.write_text(json.dumps(draft, indent=2) + '\n', encoding='utf-8')
    (output / 'floating-metadata.json').write_text(json.dumps({'rule': rule, 'highestStable': highest, 'published': published}, indent=2) + '\n', encoding='utf-8')


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
if metadata.get('restoreOutputControls'):
    from collector_fixtures import transport_envelope
    if '\t' not in restore_output or '\r' not in restore_output:
        raise SystemExit('Raw restore controls were not preserved')
    envelope = transport_envelope(restore_output, load_json(output / 'nuget.json'))
    (output / 'reference-envelope.json').write_text(envelope + '\n', encoding='utf-8')
    with (output / 'summary.md').open('a', encoding='utf-8') as summary:
        summary.write('- Raw tab/CR preservation and reference JSON envelope round-trip: PASS\n- Actual IR envelope verdict: manual\n')
for context in metadata.get('additionalGraphs', []):
    context_code, context_log = execute(['dotnet', 'restore', str(scenario_dir / context['entry']), '--locked-mode'])
    (output / (context['name'] + '-restore.log')).write_text(context_log, encoding='utf-8')
    if context_code:
        raise SystemExit(f"Additional project {context['name']} failed restore")
    context_output = output / context['name']
    context_output.mkdir(exist_ok=True)
    list_code, context_listing = execute(['dotnet', 'list', str(scenario_dir / context['entry']), 'package',
                                          '--include-transitive', '--format', 'json'])
    (context_output / 'list.json').write_text(context_listing, encoding='utf-8')
    if list_code or check_listing(build_graph(load_json(scenario_dir / context['assets']),
                                             load_json(scenario_dir / context['lock']), scenario_id), json.loads(context_listing)):
        raise SystemExit('Additional project package listing differs from assets')
    command = [sys.executable, str(ROOT / 'tools/verify_contract.py'), '--scenario', scenario_id,
               '--assets', str(scenario_dir / context['assets']), '--lock', str(scenario_dir / context['lock']),
               '--expected', str(scenario_dir / context['expected']), '--actual', str(context_output / 'nuget.json'),
               '--diff', str(context_output / 'diff.json'), '--summary', str(context_output / 'summary.md')]
    context_verify_code, _ = execute(command)
    if context_verify_code:
        raise SystemExit(f"Additional project {context['name']} graph differs")
    for check in context.get('assetChecks', []):
        evidence = load_json(scenario_dir / context['assets'])
        found = [value for target in evidence['targets'].values() for key, value in target.items()
                 if key.split('/')[0].lower() == check['package'].lower()]
        if not found or any(has_real_assets(value, field) for value in found for field in check.get('absent', [])):
            raise SystemExit('Excluded asset appeared for ' + check['package'])
    if context.get('absentAdvisories'):
        code, vulnerability_output = execute(['dotnet', 'list', str(scenario_dir / context['entry']), 'package',
                                             '--vulnerable', '--include-transitive', '--format', 'json'])
        (context_output / 'vulnerabilities.json').write_text(vulnerability_output, encoding='utf-8')
        if code or any(advisory.lower() in vulnerability_output.lower() for advisory in context['absentAdvisories']):
            raise SystemExit('Fixed project retained the affected-version advisory')
if metadata.get('afterRestore'):
    import xml.etree.ElementTree as ET
    change = metadata['afterRestore']
    tree = ET.parse(entry)
    for package in tree.getroot().iter('PackageReference'):
        if package.get('Include', '').lower() == change['package'].lower():
            package.set('Version', '[' + change['version'] + ']')
    tree.write(entry, encoding='unicode')
    after_code, after_log = execute(['dotnet', 'restore', str(entry), '--use-lock-file', '--force-evaluate'])
    (output / 'after-restore.log').write_text(after_log, encoding='utf-8')
    if after_code or graph_hash() == hashes[0]:
        raise SystemExit('Version change did not produce a different successful graph')
    after_output = output / 'after'
    after_output.mkdir(exist_ok=True)
    after_verify, _ = execute([sys.executable, str(ROOT / 'tools/verify_contract.py'), '--scenario', scenario_id,
                              '--assets', str(assets), '--lock', str(lock), '--expected', str(scenario_dir / change['expected']),
                              '--actual', str(after_output / 'nuget.json'), '--diff', str(after_output / 'diff.json'),
                              '--summary', str(after_output / 'summary.md')])
    if after_verify:
        raise SystemExit('Changed version graph differs from reviewed expectation')
if metadata.get('contextRules'):
    from context_rules import check_context_rules
    graphs = [load_json(output / 'nuget.json')] + [load_json(output / context['name'] / 'nuget.json')
                                                 for context in metadata.get('additionalGraphs', [])]
    context_errors = check_context_rules(graphs, load_json(scenario_dir / metadata['contextRules']))
    (output / 'context-rules.json').write_text(json.dumps({'passed': not context_errors, 'errors': context_errors}, indent=2) + '\n', encoding='utf-8')
    if context_errors:
        raise SystemExit('; '.join(context_errors))
if metadata.get('localFeed'):
    sources = {}
    for package in load_json(scenario_dir / 'feed.json'):
        path = Path(os.environ['NUGET_PACKAGES']) / package.lower() / '1.0.0' / '.nupkg.metadata'
        source = load_json(path)['source']
        sources[package] = source
        if Path(source).resolve() != (scenario_dir / 'feed').resolve():
            raise SystemExit('Wrong mapped source used for ' + package)
    (output / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8')
if metadata.get('mutateEvidence'):
    mutation = metadata['mutateEvidence']
    if mutation == 'missingAssets':
        assets.unlink()
    elif mutation == 'missingLock':
        lock.unlink()
    elif mutation == 'malformedAssets':
        assets.write_text('{"targets":', encoding='utf-8')
    elif mutation == 'staleAssets':
        assets.write_text(assets.read_text(encoding='utf-8').replace('13.0.3', '12.0.3'), encoding='utf-8')
    else:
        raise SystemExit('Unknown mutation: ' + mutation)
    (output / 'mutation.json').write_text(json.dumps({'mutation': mutation, 'expectedIR': 'evidence error or explicitly reduced confidence'}, indent=2) + '\n', encoding='utf-8')
    with (output / 'summary.md').open('a', encoding='utf-8') as summary:
        summary.write(f"- Evidence deliberately altered before PSE collection: {mutation}\n")
if metadata.get('fallbackFixture'):
    from collector_fixtures import configure_fallback
    configure_fallback(scenario_dir, output, entry, assets, lock, scenario_id, metadata['fallbackFixture'])
    with (output / 'summary.md').open('a', encoding='utf-8') as summary:
        summary.write('- Missing/malformed assets and real package-list fallback replay: ready\n- Actual IR fallback selection and graph verdict: manual\n')
metrics = load_json(output / 'metrics.json')
metrics['totalSeconds'] = time.perf_counter() - started
try:
    import resource
    metrics['peakChildMemoryKiB'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
except ImportError:
    metrics['peakChildMemoryKiB'] = None
    metrics['memoryNote'] = 'POSIX peak child process memory is unavailable on Windows'
(output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n', encoding='utf-8')
