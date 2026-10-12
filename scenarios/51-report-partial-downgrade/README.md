# R02: Partial NU1605 reproduction

Based on nuget_depgraph_observation_report.md (2026-10-09). The report supplied versions and observations, but not the original project files; these inputs reproduce the reported structure with original NuGet packages. Both projects target net8.0 and net9.0. Storefront references Shared.Identity.

| Project | Framework | JwtBearer | OpenIdConnect request |
|---|---|---|---|
| Storefront | net8.0 | 8.0.22 | 8.22.0 |
| Shared.Identity | net8.0 | 8.0.22 | 7.1.2 |
| Storefront | net9.0 | 9.0.9 | 8.14.0 |
| Shared.Identity | net9.0 | 9.0.9 | 7.7.1 |

Shared.Identity must have NU1605 while Storefront has no restore errors. Preserve both valid-JSON assets files and per-project diagnostics. IR may show explicitly partial evidence but must not describe the solution as a complete successful restore. A failed restore does not by itself prove stale assets.

Run verify.yml with scenario R02. The workflow installs SDK 9.0.305 for this fixture; existing cases retain SDK 8.0.419. Enable use_pse when you want to submit to IR.
