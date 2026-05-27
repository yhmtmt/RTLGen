# Design Brief

The previous measured-compute substitution selected replicated `nm64_flat` blocks because the estimator allowed all replicas to behave as a single compute fabric. That is useful as a first bound, but it hides the architectural choice between a large dynamic dispatcher and a more regular cluster hierarchy.

This job keeps the same corrected compute PPA inputs and adds a planning model with:

- static sequence-tile sharding across compute clusters,
- floor/ceil assignment of measured compute replicas to clusters,
- local SRAM treated as sharded resident KV storage,
- shared SRAM and HBM bandwidth contended by active clusters,
- explicit NoC bandwidth and hop penalties.

The result should identify whether the practical next point is a small number of large clusters, many smaller clusters, or continued memory/NOC refinement before RTL.

