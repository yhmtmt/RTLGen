# Exact Shared-Mesh Replacement Contract

- source score32 throughput: `74.137971543343` token/s
- source score32 latency: `13488.364723` us/token
- source compute clock: `48.650900` ns
- retained embodied area: `656.696176013` mm2
- replaced primitive area: `0.480367931` mm2
- maximum composed hierarchy area: `143.303823987` mm2

## Ownership

- dual_stream_compute_replicas: `296.797456000` mm2
- hbm_replay_controller: `0.028910201` mm2
- shared_kv_sram: `240.066036895` mm2
- tile_local_sram: `39.803772917` mm2
- reserved_die_area: `80.000000000` mm2

The current ranked compute area omits the primitive NoC/endpoint overhead. The measured composed hierarchy is therefore added directly to ranked compute area, while full embodied accounting replaces the old primitive overhead exactly once.

## Gates

- area: measured composed hierarchy area must be finite, positive, and no greater than maximum_composed_hierarchy_area_um2
- throughput: retain source throughput only if composed critical_path_ns does not exceed compute_clock_ns and a workload-complete composed service-cycle artifact proves no longer critical layer schedule
- energy: do not convert vectorless whole-harness power to token energy; require workload-annotated hierarchy power
- precision: inherit score32 quality only while full four-group exact RTL equivalence and zero protocol errors remain true

## Remaining Abstractions

- composed synthesis decomposition and postroute hierarchy metrics are pending
- workload-complete composed service cycles are not yet materialized as a recost input
- workload-annotated hierarchy power is pending
- vendor HBM current and off-chip energy remain external
