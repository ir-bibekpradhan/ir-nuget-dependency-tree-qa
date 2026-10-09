# S10b: chain

Every project context has a separate expected graph, so matching target frameworks do not merge different package versions.

App -> Core -> Data. Dapper flows to App, Core's private Newtonsoft does not. Core's own graph still includes Newtonsoft.
