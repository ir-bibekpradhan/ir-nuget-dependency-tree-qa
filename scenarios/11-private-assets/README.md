# S16 - private-assets

Proves that a PrivateAssets package remains visible in its own restored graph while its flow to consumers is constrained.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

