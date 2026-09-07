# All-cluster numerical collection

All sixteen concrete endpoint RTL replays passed their exact reference-row
checks. `all_cluster_numerical_payloads.json` retains 512 observed rows per
endpoint (8192 total), all release cycles, 512 exact expected finalized root
rows, and seven source identities. Each recorded source hash was verified
against the unchanged source before use. The archived JSON is content-identical
to the collector output and produces identical leaf/root/release sidecars.

The p54 endpoints 0–7 have first output cycles 17432, 33824, 50216, and 66608;
their final cycle is 66735. The p53 endpoints 8–15 have first cycles 17437,
33829, 50221, and 66613; their final cycle is 66740. These are separate concrete
cluster replays, not one simultaneously instantiated full-cluster simulation.

The original collector output SHA-256 is
`f82c54c993854f8cc29a1307b4a8443ae442b4b0687df57bceffe9c3fb9b4eed`.
The archive uses compact serialization; file-byte hashes therefore differ.
The numerical shared-mesh replay is running and has no passing result yet.

Scope: these are arithmetic-stress-fixture values. The fixture varies Q with
placement and must not be relabeled canonical resident decoder queries.
Canonical mapped attention equivalence, simultaneous producer/mesh
backpressure, routed composition, CDC, and activity-backed power remain open.
