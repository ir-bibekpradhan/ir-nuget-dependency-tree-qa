# S14 - casing-normalization

Proves that NuGet package IDs compare case-insensitively while their canonical display identity remains stable.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

