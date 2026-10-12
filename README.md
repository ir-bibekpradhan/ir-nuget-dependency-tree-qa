# InvisiRisk NuGet dependency-tree QA

54 isolated fixtures cover the 24 scenario families in the approved NuGet QA plan plus five observation-report regressions. Ordinary resolution fixtures use original NuGet.org packages. Only the local-feed and depth/fan-out fixtures use deliberately synthetic packages, as requested in the plan.

See [COVERAGE.md](COVERAGE.md) for scenario IDs, package choices and expected IR behavior. Each folder has scenario.json, project files, a README and reviewed expected graphs. Deterministic fixtures have fixed inputs; floating and advisory checks use current feed metadata.

## Run in GitHub Actions

Open **Actions → NuGet dependency graph QA → Run workflow**.

- Choose `all` to run every fixture, `deterministic` for stable regression checks, or `nightly` for floating, vulnerability and scale cases.
- Set `scenario` to one ID, such as `S04`, or leave `all`.
- Use `R*` to run only the five observation-report fixtures, or comma-separated IDs such as `R01,R02`. See [the report regression guide](docs/observation-regressions.md).
- Set `phase` to `1`, `2`, `3`, or `all`.
- Leave `use_pse` checked to submit scans to IR. Uncheck it for NuGet reference verification only. Push/PR checks verify references without submitting scans.

The normal workflow is [.github/workflows/verify.yml](.github/workflows/verify.yml). Nightly cases also have a scheduled workflow. Native Windows reference restore has a separate manual workflow; the IR matrix restores both Linux and Windows RID graphs on Linux.

Scheduled nightly checks verify NuGet references. Submit nightly IR scans by manually running that workflow with use_pse enabled.

PSE uses the repository's `IR_TOKEN` secret and https://app.stage.invisirisk.com. No credential is committed. With a configured secret, each matrix job submits a separate scenario scan. PSE setup/finalization errors remain visible; an unavailable IR service can fail a job even when NuGet verification passes.

## Ground truth and pass criteria

The SDK is pinned to **8.0.419**. A root NuGet.Config clears inherited sources, and package/HTTP caches are isolated per scenario. Fixed-version fixtures restore against committed locks where applicable. Unlocked, floating, synthetic and warning fixtures intentionally generate fresh locks.

R01/R02 pin SDK **9.0.305** in their own global.json files to restore net8.0 and net9.0 together. Workflow SDK selection follows scenario metadata; existing SDK 8 fixtures retain their version.

For every successful restore, the verifier compares complete package/project nodes, root edges, dependency edges, requested constraints, direct flags and all parent paths with expected graphs, separated by framework/RID/project context. Duplicate nodes/edges/paths and dangling edges fail verification. Shared dependencies must retain every incoming path.

Artifacts include restore logs, assets, locks, package listings, normalized graphs, diff.json, summary.md, hashes and timing/memory metrics. Nightly vulnerability checks record advisory evidence. S24 performs three restores, requires identical graph hashes, then changes Serilog's version and checks a second reviewed graph.

For failed restores, PASS means the intended failure and NuGet error code occurred. For S20 evidence-corruption fixtures, the valid baseline is checked first and then altered before PSE collection. IR should flag the missing/malformed/stale evidence or explicitly report reduced confidence. Read each scenario README for its expected result.

NuGet-reference PASS is independent of the manual IR verdict. Compare IR's displayed/exported graph with the artifact's nuget.json and expected graph. Optional IR_GRAPH_PATH accepts an already exported normalized graph; no IR API endpoint is assumed.

## Local use

With .NET SDK 8.0.419 and Python 3:

```bash
python tools/validate_scenarios.py
python tools/run_scenario.py scenarios/04-shared-dependency
python -m unittest discover -s tools -p "test_*.py"
```

The capture workflow generates candidate contracts for maintainer review. It does not automatically replace expected graphs or approve scanner behavior.

## Release gates

Run Phase 1 five consecutive times with identical stable graphs. Then validate Phase 2 against IR, followed by Phase 3 scale/repetition checks. Record IR's verdict separately, including evidence confidence, advisory version association, UI/API/SBOM agreement and scan identity. The repository supplies reproducible inputs and reference evidence; those IR product verdicts are assessed when you run it.
