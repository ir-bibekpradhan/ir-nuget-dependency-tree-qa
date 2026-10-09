# S11 - rid-specific-dependencies

Proves that the linux-x64 target keeps runtime-specific SQLite packages and native relationships separate from framework-only graph data.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

