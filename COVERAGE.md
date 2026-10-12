# Coverage against the approved PDF

| PDF family | Runnable fixture IDs | Expected behavior |
|---|---|---|
| S01 Exact version | S01 | Newtonsoft.Json 13.0.3, one direct identity |
| S02 Minimum/unpinned | S02 | Minimum 12.0.3 resolves to 12.0.3, not automatically latest |
| S03 Floating/prerelease | S03, S03b, S03c | Highest matching stable version for 13.* and *; preserve exact beta label |
| S04 Direct + transitive shared | S04 | Serilog 3.1.1 is direct and also a child of Console 5.0.1 |
| S05 Diamond | S05, S05b | Configuration branches and Console/File branches retain shared descendants |
| S06 Direct wins | S06, S06b | Serilog override and Logging/DI override resolve the direct higher version |
| S07 Warning/downgrade/conflict | S07a, S07b, S07c | NU1605 failure, explicitly allowed NU1605 warning, NU1107 conflict |
| S08 Restore/lock variants | S08a, S08b, S08c, S01 | Unlocked, stale locked failure, primed offline, normal locked restore |
| S09 Multiple frameworks | S09, S09b | Different versions by framework; conditional JSON package absent from net8 graph |
| S10 Project references | S10, S10b | Two/three-level project chains; private package stays in its owning project |
| S11 Runtime contexts | S11, S11b | Linux and Windows RID graphs stay distinct; native Windows reference available |
| S12 CPM | S12, S12b | Central version and per-project VersionOverride honored |
| S13 Transitive pinning | S13 | Centrally pinned Serilog remains transitive, not a fabricated direct reference |
| S14 Identity normalization | S14, S14b | Case-insensitive IDs and equivalent trailing-zero revision |
| S15 Feeds/source mapping | S15, S15b | NuGet.org mapping plus deterministic local feed and duplicate-source exclusion |
| S16 Asset/private flow | S16, S16b | Private packages/analyzers do not flow to App; excluded runtime assets tested |
| S17 Direct vulnerability | S17, S17a | Original ImageSharp 4.0.0 fixture plus known affected Newtonsoft version |
| S18 Shared transitive vulnerability | S18 | Newtonsoft shared through original MVC/JsonPatch parents |
| S19 Same package, two versions | S19a, S19b, S19c | Distinct roots/versions; affected-version advisory absent in fixed context |
| S20 Invalid evidence | S20a–S20d | Missing assets, malformed assets, missing lock, stale assets flagged or confidence reduced |
| S21 Incomplete restores | S21a–S21c | Unknown package, closed feed, partial solution must not become complete successful trees |
| S22 Large real graph | S22, S22b | Azure baseline plus EF SQL Server/Azure/AWS graph; preserve all paths and record metrics |
| S23 Synthetic scale | S23 | 50-package chain, 20-way shared fan-out, 72 package nodes |
| S24 Repeat/change | S24 | Three equal restore hashes, then reviewed changed-version graph |
| Additional warning | X01 | Duplicate reference produces NU1504 without duplicate component identity |

Synthetic feed tests emulate a private feed locally without credentials. An authenticated production/private-registry run can reuse the package identities but requires that feed's URL and secret configuration. Linux jobs restore both RID variants; the separate Windows workflow provides native NuGet ground truth, without assuming Windows PSE bootstrap support.

## Manual IR acceptance checklist

- Match each scenario's roots, resolved versions, direct/transitive status, edges and full paths against its artifact.
- Keep framework, RID and project contexts separate. Do not merge two versions merely because IDs match.
- Confirm failed/partial restores and invalid evidence have accurate status/confidence.
- Attach advisories to the affected package version and retain every shared path to it.
- Repeat stable Phase 1 scans five times. Compare UI/API/SBOM identities and paths across repeated scans, then confirm the changed S24 version removes stale results.

The workflows verify NuGet ground truth. IR product acceptance is recorded separately when you run the scans; PSE submission alone does not prove graph accuracy.

## Observation report regressions (2026-10-09)

| ID | Added coverage |
|---|---|
| R01 | Storefront -> Shared.Identity, net8/net9, same JwtBearer parent identity with different resolved children by project, explicit context edge assertions |
| R02 | Report's partial NU1605 downgrade: Storefront success and Shared.Identity failure; preserve valid-JSON assets and separate diagnostics |
| R03 | Missing assets and lock force a controlled real package-list fallback input |
| R04 | Malformed assets plus real package-list fallback input |
| R05 | Tabs, bare CR and CRLF in real restore output; escaped reference JSON envelope round-trip |

R01 is the successful companion to the report's failed R02. R03-R05 are robustness extensions, not findings proved by the report. Their reference checks validate the inputs; actual production collector fallback choice and envelope handling are checked in the manual PSE run. No stale-assets claim is inferred from R02's restore failure.
