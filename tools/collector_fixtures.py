import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from graph_contract import build_graph, check_listing, load_json


def install_wrapper(folder, real_dotnet, *, fallback=False, restore_controls=False):
    directory = folder / '.qa'
    binary_dir = directory / 'bin'
    binary_dir.mkdir(parents=True, exist_ok=True)
    wrapper = binary_dir / 'dotnet'
    shutil.copy2(Path(__file__).with_name('dotnet_fixture.py'), wrapper)
    wrapper.chmod(0o755)
    (directory / 'wrapper-config.json').write_text(json.dumps({'realDotnet': real_dotnet, 'fallback': fallback,
                                                              'restoreControls': restore_controls}), encoding='utf-8')
    os.environ['PATH'] = str(binary_dir) + os.pathsep + os.environ['PATH']
    return directory, binary_dir


def configure_fallback(folder, output, entry, assets, lock, scenario_id, mode):
    real_dotnet = shutil.which('dotnet')
    json_result = subprocess.run([real_dotnet, 'list', str(entry), 'package', '--include-transitive', '--format', 'json'],
                                 cwd=folder, capture_output=True, timeout=300)
    text_result = subprocess.run([real_dotnet, 'list', str(entry), 'package', '--include-transitive'],
                                 cwd=folder, capture_output=True, timeout=300)
    if json_result.returncode or text_result.returncode:
        raise ValueError('Could not capture the real package listings')
    listing = json.loads(json_result.stdout)
    errors = check_listing(build_graph(load_json(assets), load_json(lock), scenario_id), listing)
    if errors:
        raise ValueError('; '.join(errors))
    directory, binary_dir = install_wrapper(folder, real_dotnet, fallback=True)
    (directory / 'package-list.json').write_bytes(json_result.stdout)
    (directory / 'package-list.text').write_bytes(text_result.stdout)
    replay = subprocess.run(['dotnet', 'list', str(entry), 'package', '--include-transitive', '--format', 'json'],
                            cwd=folder, capture_output=True, timeout=30)
    if replay.returncode or json.loads(replay.stdout) != listing:
        raise ValueError('Fallback replay did not preserve the real package listing')
    shutil.copy2(directory / 'package-list.json', output / 'fallback-list.json')
    shutil.copy2(directory / 'package-list.text', output / 'fallback-list.txt')
    if mode == 'missing':
        assets.unlink()
    elif mode == 'malformed':
        assets.write_text('{"targets":', encoding='utf-8')
    else:
        raise ValueError('Unknown fallback mode')
    lock.unlink()
    github_path = os.environ.get('GITHUB_PATH')
    if github_path:
        with open(github_path, 'a', encoding='utf-8') as handle:
            handle.write(str(binary_dir) + '\n')
    contract = {'baselineVerified': True, 'assetsState': mode, 'lockRemoved': True,
                'fallbackEvidence': 'real dotnet list output replayed by a scoped PATH wrapper',
                'irVerdict': 'manual: preserve IDs/versions; do not invent edges from a flat listing',
                'collectorInvocationVerified': False}
    (output / 'fallback-contract.json').write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')
    return contract


def transport_envelope(restore_output, graph):
    envelope = {'schemaVersion': 1, 'restoreOutput': restore_output, 'graph': graph}
    encoded = json.dumps(envelope, ensure_ascii=False)
    decoded = json.loads(encoded)
    if decoded != envelope or '\t' in encoded or '\r' in encoded:
        raise ValueError('Envelope did not preserve and escape control characters')
    return encoded
