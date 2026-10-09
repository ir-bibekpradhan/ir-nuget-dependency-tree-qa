# S08b - stale-lockfile

Proves that locked restore rejects a project and lockfile mismatch with NU1004. IR must represent the build failure rather than stale graph data.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

