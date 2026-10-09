# S19a: vulnerable-version-context

Run: `python tools/run_scenario.py scenarios/21-version-vulnerable`.

Uses real NuGet.org packages. The reviewed graph is in expected/graph.json.
Compare S19a and S19b as separate project contexts. The same package has different versions; the Newtonsoft advisory must stay attached to its affected version.
