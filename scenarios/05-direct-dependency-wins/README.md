# S06 - direct-dependency-wins

Proves NuGet direct-dependency-wins behavior. Direct Serilog 4.1.0 overrides the console sink's lower minimum while preserving the sink-to-Serilog edge.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

