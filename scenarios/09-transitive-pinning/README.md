# S13 - transitive-pinning

Proves that Central Package Management pins Serilog transitively to 4.1.0 without incorrectly classifying it as an ordinary direct PackageReference.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

