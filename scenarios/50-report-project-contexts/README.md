# R01: Project/framework context reproduction

Based on nuget_depgraph_observation_report.md (2026-10-09). The report supplied versions and observations, but not the original project files; these inputs reproduce the reported structure with original NuGet packages. Both projects target net8.0 and net9.0. Storefront references Shared.Identity.

| Project | Framework | JwtBearer | OpenIdConnect request |
|---|---|---|---|
| Storefront | net8.0 | 8.0.22 | 8.22.0 |
| Shared.Identity | net8.0 | 8.0.22 | 7.1.2 |
| Storefront | net9.0 | 9.0.9 | 8.14.0 |
| Shared.Identity | net9.0 | 9.0.9 | 8.0.1 |

This successful companion raises Shared.Identity's net9 request to the required minimum 8.0.1; R02 retains the report's failing 7.7.1. Every expected graph is scoped by project and framework. Verify the six explicit edges in expected/context-rules.json. Never take the Shared.Identity 7.1.2 child for Storefront, drop the net9 JwtBearer child, or flatten away Storefront -> Shared.Identity.

Run verify.yml with scenario R01. The workflow installs SDK 9.0.305 for this fixture; existing cases retain SDK 8.0.419. Enable use_pse when you want to submit to IR.
