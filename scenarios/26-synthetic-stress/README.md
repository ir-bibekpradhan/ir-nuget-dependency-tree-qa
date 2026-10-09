# S23: SyntheticStress

This is an explicitly synthetic fixture from the approved PDF. All other resolution tests use original NuGet.org packages.

A 50-package chain and 20 branches sharing one package yield 72 package nodes. All 20 incoming paths to the shared component must survive.

Packages are generated deterministically from feed.json before restore. expected/graph.json was constructed independently from that specification. No private-feed credentials are needed.
