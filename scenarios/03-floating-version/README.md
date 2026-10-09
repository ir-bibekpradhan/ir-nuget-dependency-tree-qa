# S03 - floating-version

Proves that a floating 13.* request resolves to the current highest matching package. This is intentionally non-deterministic and belongs in the nightly workflow.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

