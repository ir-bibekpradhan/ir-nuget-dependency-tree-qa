# Run the observation-report regressions

Open Actions -> NuGet dependency graph QA -> Run workflow. Set mode=all, scenario=R*, phase=all. Leave use_pse checked for IR scans; uncheck it to verify reference inputs only. For one reproduction use R01 or R02. Original scenario IDs remain available.

## R01: Successful graph/context companion

Storefront references Shared.Identity. Both target net8.0 and net9.0. Assert these edges within their respective project and framework contexts:

| Project | Framework | Parent | Resolved child |
|---|---|---|---|
| Storefront | net8.0 | JwtBearer 8.0.22 | OpenIdConnect 8.22.0 |
| Shared.Identity | net8.0 | JwtBearer 8.0.22 | OpenIdConnect 7.1.2 |
| Storefront | net9.0 | JwtBearer 9.0.9 | OpenIdConnect 8.14.0 |
| Shared.Identity | net9.0 | JwtBearer 9.0.9 | OpenIdConnect 8.0.1 |

Also require Storefront -> Shared.Identity in both framework graphs. The same parent package version must not cause one project's child version to overwrite another's. OpenIdConnect may also be a direct root dependency, but that must not remove its incoming JwtBearer edge.

JwtBearer [8.0.22](https://www.nuget.org/packages/Microsoft.AspNetCore.Authentication.JwtBearer/8.0.22) requires OpenIdConnect >=7.1.2; [9.0.9](https://www.nuget.org/packages/Microsoft.AspNetCore.Authentication.JwtBearer/9.0.9) requires >=8.0.1. R01 changes the report's failing Shared.Identity net9 request to 8.0.1 so all four contexts have successful ground truth. Full graphs and an independent six-edge contract are committed under expected/.

## R02: Partial NU1605 reproduction

R02 retains Shared.Identity's net9 request 7.7.1. The solution restore must fail with NU1605. Storefront must have no restore errors, while Shared.Identity's assets must record NU1605. The test stores both assets as evidence and records project states and content hashes.

IR must show failure/incompleteness accurately. Displaying explicitly partial evidence is allowed; labeling the entire solution a complete successful graph is a defect. Fresh failed-restore assets are not automatically stale. The report alone does not prove stale evidence.

The original project files were not attached to the observation report. These fixtures reproduce its package versions, target frameworks and local project relationship rather than asserting byte-for-byte identity with those unavailable files.

## R03/R04: Package-list fallback inputs

First verify a real Serilog/Console restore and capture both dotnet list JSON and text output. Then remove assets (R03) or corrupt their JSON (R04), and remove the lock. A scoped dotnet wrapper replays those real listings for package-list commands and delegates all other commands to the genuine executable.

The wrapper emits IR_QA_LIST_FALLBACK_REPLAY when selected. Confirm fallback invocation in the production collector's post-step diagnostics. If the collector uses a different executable/path or never invokes the listing, record the case as not exercised rather than a pass. NuGet/reference verification tests the replay inputs only.

The fallback must keep correct IDs/versions and direct flags. A flat list does not prove transitive edges; IR should label reduced relationship evidence unless it reconstructs and verifies those edges from another source. Compare with the preserved baseline nuget.json. These deterministic inputs use original packages, not fabricated dependency metadata.

## R05: Restore output controls and envelope validity

The real restore runs through a wrapper adding a tab, a bare carriage return and CRLF. Its exit code is preserved. Raw bytes are decoded without newline conversion, and the reference envelope must preserve the string exactly after JSON decoding. Tabs and CR must be escaped within JSON strings.

Inspect IR's actual collector output/envelope in the PSE run: it must remain valid JSON and preserve the graph. reference-envelope.json validates the fixture's reference serialization, not the unseen production collector implementation.

All cases provide logs and expected/reference evidence as workflow artifacts. No new token or API integration is introduced.
