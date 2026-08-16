# Design Brief

The recost retains the measured compute array, finite endpoint, composed mesh,
fixed on-chip SRAM capacity, and calibrated HBM-controller parameters. It then
rebuilds each candidate's upstream schedule row.

For each wave, one global controller serves `active_clusters * tile_hbm_bytes`.
The controller and compute clocks remain separate and are compared in time,
not by comparing raw cycle counts from different domains. Wave release cadence
is the slower of attention arithmetic and aggregate HBM service, after which
the complete finite-endpoint NoC schedule is replayed.

MHA changes QKV projection work from `H^2 + 2H(H/8)` to `3H^2`, expands the KV
cache and KV writes by eight, and recomputes HBM command energy. Attention QK
and value MACs, reduction payload, compute-array area, and fixed shared-SRAM
bytes do not scale with KV-head count.
