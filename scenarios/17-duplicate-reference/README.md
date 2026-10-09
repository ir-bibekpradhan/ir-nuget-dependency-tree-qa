# X01 - duplicate-reference-warning

Proves that duplicate PackageReference items emit NU1504 but still resolve to one package node.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

