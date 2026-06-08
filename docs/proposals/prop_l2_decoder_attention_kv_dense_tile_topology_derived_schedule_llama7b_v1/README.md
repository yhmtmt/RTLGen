# Llama7B Dense Tile Topology-Derived Schedule

This proposal queues the follow-on L2 scheduler run after the topology/scheduler
validity filter. The job consumes the compact valid topology-pair artifact and
reruns the dense-tile Llama7B clustered schedule using topology-derived NoC
service rows.

The key correction is that `cluster_count`, `bank_count`,
`local_sram_fraction`, `reduction_strategy`, link width, virtual channels, and
worst-hop latency are coupled. The job no longer sweeps abstract
`noc_bandwidth_bytes_per_cycle` and `noc_hops` independently.

Expected output:

- revised Llama7B dense-tile latency frontier under valid topology service rows
- best rows by topology, scheduler, die size, and reduction policy
- explicit comparison to the previous abstract 65kB/cycle one-hop NoC target
