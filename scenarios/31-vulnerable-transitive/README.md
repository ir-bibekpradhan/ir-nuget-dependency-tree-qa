# S18: VulnerableTransitive

Uses pinned original NuGet.org packages. Review expected/graph.json for every node, edge and path after restore.
Newtonsoft.Json must be transitive and shared between the JSON formatter and JsonPatch paths. Its reported advisories must remain attached to the resolved version.
