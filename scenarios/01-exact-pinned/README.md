# S01 - exact-version

Proves that an exact NuGet range resolves to one direct package at exactly 13.0.3. Newtonsoft.Json is a stable leaf package, so unexpected children are also detectable.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

