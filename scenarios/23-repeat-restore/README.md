# S24: repeat-restore-consistency

Run: `python tools/run_scenario.py scenarios/23-repeat-restore`.

Uses real NuGet.org packages. The reviewed graph is in expected/graph.json.
Three fresh assets files from three restores must produce identical canonical graph hashes.
