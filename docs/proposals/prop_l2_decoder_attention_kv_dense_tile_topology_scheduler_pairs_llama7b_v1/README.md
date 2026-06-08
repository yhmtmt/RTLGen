# Llama7B Dense Tile Topology/Scheduler Pairs

This proposal queues a focused L2 job to validate logically compatible NoC
topology, scheduler, reducer, bank-placement, link-width, and virtual-channel
pairs for the Llama7B dense-tile attention frontier.

The previous reduction/NoC frontier used independent service knobs such as
`noc_bandwidth_bytes_per_cycle=65536`, `noc_hops=1`, and
`reduction_strategy=cluster_tree`. That was useful for locating pressure, but
it can combine assumptions that do not correspond to a realizable topology.
This job derives service envelopes from explicit topology/link choices and
records invalid-pair reasons before the next scheduler/performance sweep.

Expected output:

- a valid-pair matrix across `cluster_tree`, `mesh2d`, `ring`, and `crossbar`
- explicit invalid reasons for topology/scheduler/reducer/bank combinations
- derived aggregate/per-cluster payload service and hop counts
- a shortlist to feed into the next clustered scheduler run
