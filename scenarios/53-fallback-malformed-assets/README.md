# R04: FallbackMalformedAssets

Restores original Serilog 3.1.1 and Console 5.0.1, verifies the full graph and preserves baseline assets/lock/listing outside the scanner work directory.

After successful verification, assets are replaced with malformed JSON and the lock is removed. A scoped dotnet PATH wrapper supplies both JSON and text listings captured from the real restore, while delegating all other commands to the original dotnet executable. This makes the package-list fallback input deterministic without invented package data. The wrapper writes IR_QA_LIST_FALLBACK_REPLAY on invocation.

IR must preserve package IDs/versions. A flat list alone cannot establish Console -> Serilog; IR should identify reduced relationship evidence or prove reconstructed edges against the preserved full graph. Confirm the collector actually selected the wrapper fallback from post-collection diagnostics before marking the IR test passed.

Run verify.yml with scenario R04 on Linux. use_pse submits the input to IR. NuGet/reference PASS establishes fixture correctness; it does not automatically approve the production collector. The observation report did not demonstrate these robustness cases; they are additional tests.
