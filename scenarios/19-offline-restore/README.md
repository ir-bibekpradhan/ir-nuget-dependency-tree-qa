# S08c: primed-offline-restore

Run: `python tools/run_scenario.py scenarios/19-offline-restore`.

Uses real NuGet.org packages. The reviewed graph is in expected/graph.json.
Prime an isolated cache, then restore with all sources replaced by an empty local feed; no remote source is available during the offline restore.
