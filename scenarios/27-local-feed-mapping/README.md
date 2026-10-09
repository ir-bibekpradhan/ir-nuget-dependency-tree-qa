# S15b: LocalFeedMapping

This is an explicitly synthetic fixture from the approved PDF. All other resolution tests use original NuGet.org packages.

The same package bytes appear in two local feeds. Source mapping permits only the local feed; the duplicate source must not be used.

Packages are generated deterministically from feed.json before restore. expected/graph.json was constructed independently from that specification. No private-feed credentials are needed.
