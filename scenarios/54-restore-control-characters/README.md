# R05: RestoreOutputControls

Restores original Serilog 3.1.1 and Console 5.0.1, verifies the full graph and preserves baseline assets/lock/listing outside the scanner work directory.

A scoped wrapper preserves the actual restore exit status and adds a tab, bare carriage return and CRLF to restore stdout. The runner captures bytes without universal-newline conversion. reference-envelope.json must parse and reproduce the original control characters exactly, with JSON escaping. Actual IR collector-envelope validity remains a manual acceptance check in the PSE run.

Run verify.yml with scenario R05 on Linux. use_pse submits the input to IR. NuGet/reference PASS establishes fixture correctness; it does not automatically approve the production collector. The observation report did not demonstrate these robustness cases; they are additional tests.
