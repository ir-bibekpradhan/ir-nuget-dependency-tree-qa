# S04 - direct-and-transitive-same-package

Proves that Serilog 3.1.1 is one component with two paths: directly from the project and through Serilog.Sinks.Console. IR must retain both paths without duplicating the node.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

