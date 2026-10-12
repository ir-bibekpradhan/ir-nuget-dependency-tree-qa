#!/usr/bin/env python3
"""Replay real captured package-list output; delegate every other command to real dotnet."""
import json
import os
from pathlib import Path
import subprocess
import sys

directory = Path(__file__).resolve().parent.parent
config = json.loads((directory / 'wrapper-config.json').read_text(encoding='utf-8'))
arguments = sys.argv[1:]
if config.get('fallback') and 'list' in arguments and 'package' in arguments:
    kind = 'json' if 'json' in arguments or '--format=json' in arguments else 'text'
    with (directory / 'invocations.jsonl').open('a', encoding='utf-8') as log:
        log.write(json.dumps({'command': 'list-package', 'format': kind}) + '\n')
    sys.stdout.buffer.write((directory / ('package-list.' + kind)).read_bytes())
    raise SystemExit(0)
if config.get('restoreControls') and arguments and arguments[0] == 'restore':
    result = subprocess.run([config['realDotnet'], *arguments], capture_output=True)
    sys.stdout.buffer.write(b'IR_QA_CONTROL_PROBE\ttab\rcarriage-return\r\n' + result.stdout)
    sys.stderr.buffer.write(result.stderr)
    raise SystemExit(result.returncode)
os.execv(config['realDotnet'], [config['realDotnet'], *arguments])
