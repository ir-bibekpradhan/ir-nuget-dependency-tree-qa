# S10 - multi-project-solution

Proves that a project reference carries the library's Newtonsoft.Json dependency into the application graph while preserving the application's direct Serilog dependency.

The committed expected graph is the reviewed contract. NuGet assets, lock data, package listings, and any supplied IR export are compared independently.

