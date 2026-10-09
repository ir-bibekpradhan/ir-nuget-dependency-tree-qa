# InvisiRisk NuGet dependency-tree QA

Runnable regression suite for comparing InvisiRisk dependency trees with NuGet's resolved graph. The fixtures use real packages from NuGet.org and cover successful resolution, warnings, expected failures, framework-specific graphs, project references, Central Package Management, runtime packages, and vulnerable packages.

## Scenarios

| Scenario | Coverage |
|---|---|
| `01-exact-pinned` | Exact direct version |
| `02-minimum-version` | Non-pinned minimum version |
| `03-floating-version` | Floating major version |
| `04-shared-dependency` | Direct and transitive paths to one shared node |
| `05-direct-dependency-wins` | Direct higher version overrides a transitive minimum |
| `06-diamond-dependency` | Two branches converge on shared dependencies |
| `07-multi-target` | Different versions for different target frameworks |
| `08-central-package-management` | Versions inherited from `Directory.Packages.props` |
| `09-transitive-pinning` | Centrally pinned transitive dependency |
| `10-multi-project` | Project reference plus package dependencies |
| `11-private-assets` | Test/build dependency with `PrivateAssets=all` |
| `12-vulnerable-package` | Real vulnerable ImageSharp version and its child |
| `13-rid-specific` | Runtime-specific SQLite packages |
| `14-deep-graph` | Larger, deeper Azure dependency graph |
| `15-case-normalization` | Case-insensitive NuGet package identity |
| `16-source-mapping` | Explicit NuGet source mapping |
| `17-duplicate-reference` | Successful restore with duplicate-reference warning |
| `90-downgrade-failure` | Expected `NU1605` downgrade failure |
| `91-conflicting-constraints` | Expected incompatible-version restore failure |
| `92-stale-lockfile` | Expected locked-restore mismatch failure |

## Ground truth

Every successful scenario is checked against `obj/project.assets.json`. The verifier validates resolved nodes, versions, root/package edges, shared incoming paths, framework/RID separation, minimum graph size, and graph depth. CI also records `packages.lock.json`, package listings, restore logs, and normalized actual graphs as artifacts.

Run the complete suite with .NET 8 and Python 3:

```bash
python tools/run_suite.py
```

## InvisiRisk

The GitHub Actions workflow conditionally starts InvisiRisk PSE when the repository secret `IR_TOKEN` is available. All NuGet restores and the Docker baseline then run through PSE. No token or certificate is stored in the repository.

The primary UI/API assertions are:

- Exact resolved package ID and version
- Correct direct/transitive classification
- Correct parent-child edges and full paths
- One component identity for shared nodes, with every incoming path retained
- Separate graphs for each framework/RID
- No successful dependency tree for failed restores
- Vulnerabilities attached only to the affected package version

