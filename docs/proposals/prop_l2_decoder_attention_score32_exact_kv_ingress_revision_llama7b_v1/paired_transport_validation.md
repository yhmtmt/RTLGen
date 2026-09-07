# Paired K transport validation

The p53 and p54 capacity-wrapper transport diagnostics passed locally on
2026-09-07 in 358.02 and 356.89 seconds, respectively. The original attempts both terminated at the
300-second subprocess limit, without an RTL assertion result. The instrumented
p54 run completed successfully with the same checked counts as p53.

The passing runs use the real paired-mode capacity scheduler, refill
barrier, source dispatch, packetizers, destination ownership guard, packet
mesh, and three transpose buffers of the selected p53/p54 family. Each checks:

- 69,632 real resident-cache refill writes, with no duplicate writes or reads
  before initialization;
- the first K head of layer-0 tiles 0, 1, and 2, including tile 2's packed
  resident prefix and alternating resident/HBM source ownership;
- 12,288 canonical ingress flits in exact paired address order;
- 12,288 transpose output beats using block-slot-varying payloads;
- 394 accepted and completed descriptors, 8,704 resident reads, and 73,216
  HBM reads under source, refill, and output stalls.

Each compiled fixture was compared byte-for-byte with the baseline fixture
after substitution of its producer count. Baseline fixture SHA-256:
`65e9ae09a68a3ffee103b91d5b99ae17e2b530d5d4fc2e52141531e6fb855a7b`.
The diagnostic runner at launch had SHA-256
`2bff9779f204c82cdfb7b01925caec19719d6b5fc57dfa2a705f0a7578db63ea`.
It ran with `RTLGEN_PAIRED_MESH_TIMEOUT=1800`; the default allowance was
subsequently raised to that value based on the measured wall-clock runtime.

This is bounded transport evidence, not full-model numerical closure. The
fixture stops after three heads and does not assert full-model `done`; it
does not execute the downstream K/Q stage, V consumption, score production,
or the final attention reduction. Its block-constant payload cannot detect
every intra-block permutation. Separate all-head p53/p54 transpose tests cover
stream/token/dimension-varying values and producer metadata. No routed area,
timing frequency, activity power, HBM-controller implementation, or Pareto
membership is established by this diagnostic. Stronger integrated p53 and p54
runs using stream/token/dimension-varying payloads are now live; their results
are not included in these passing baseline claims.
