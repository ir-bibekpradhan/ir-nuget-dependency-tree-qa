# S16b: flow

Every project context has a separate expected graph, so matching target frameworks do not merge different package versions.

The library includes private Newtonsoft and analyzers; App must not inherit those private packages. System.Text.Json remains a dependency while its runtime assets are excluded.
