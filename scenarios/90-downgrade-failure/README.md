# S07a - downgrade-failure

Proves that a direct downgrade is surfaced as NU1605 and never becomes a misleading successful dependency tree.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

