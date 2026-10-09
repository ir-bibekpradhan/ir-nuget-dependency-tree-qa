# S09 - multi-targeting

Proves that net8.0 and netstandard2.0 retain separate dependency graphs and different Newtonsoft.Json versions. Packages from one target must never leak into the other.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

