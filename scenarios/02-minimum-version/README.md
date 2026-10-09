# S02 - non-pinned-minimum-version

Proves NuGet's lowest-applicable-version behavior for an unbracketed minimum. The resolved version must remain distinct from floating or exact-range semantics.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

