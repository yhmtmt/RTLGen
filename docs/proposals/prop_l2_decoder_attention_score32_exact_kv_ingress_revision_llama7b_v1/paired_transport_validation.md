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
membership is established by this diagnostic.

## Nonuniform payload result

The stronger p53 and p54 integrated transport cases passed in 765.60 and 781.00
seconds, respectively. Each checks
the same refill, source-read, paired-address, output, and descriptor counts
with payload bytes varying by block slot, stream, token, and dimension. Both
canonical mesh ejection values and all transpose output bytes match the
fixture's expected values. This supersedes the block-constant p53/p54 data checks
for this three-head fixture, not its full-model or physical limitations.

Both executed fixtures match commit `397546ae` after producer substitution.
Fixture SHA-256:
`c24017e9ac7cd6e3f92a393e62bee641a079666980141ca945dfded885dac860`.
Runner SHA-256:
`74abac3b23736b152e4e7838fc9619c8e1785532e333ef64532002709a3f50db`.
Separate continuous mesh-to-wide-K/Q-stage p53 and p54 tests are live; neither
pending outcome is claimed here. Wall-clock test runtime is not simulated
workload latency or PPA.

## Continuous K/Q diagnostic

The initial continuous p53 mesh-to-stage run failed on producer 0, beat 0.
A short audit of all 128 query words in each of the three stages reproduced
unknown data at query dimension 0. The fixture's `always @*` query generator
had not evaluated before the first write; `always_comb` gives the required
startup evaluation. The short initialization audit passes with that change.
This is a testbench correction, not a change to the K/Q stage RTL. The corrected
full p53 run is live and must pass independently before continuous K/Q closure
can be claimed. The older p54 run used the same defective initialization and
cannot support a passing composed-path claim.
