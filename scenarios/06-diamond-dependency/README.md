# S05 - diamond-shared-dependency

Proves that two configuration branches converge on shared Microsoft.Extensions components. All incoming edges must be retained while each package version appears once per target.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

