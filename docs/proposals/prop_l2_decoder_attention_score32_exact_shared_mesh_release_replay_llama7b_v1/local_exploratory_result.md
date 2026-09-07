# Exploratory measured-release mesh replay

The local full test passed with 73,845 service cycles: VC0 completed at 7,785,
VC1 at 73,845. Both inter-VC overlap counts were zero. Payload checks covered
60,928 VC0 flits and 512 exact VC1 rows; the model matched 8,192 source
handshakes and 79,396 arbitration decisions. The eager comparison remained
15,769 cycles.

`local_exploratory_result.json` preserves the emitted report unchanged. Source
files were edited while its Python processes were running. Its end-of-run
source hashes therefore do not identify every in-memory version used. Treat
this as exploratory execution evidence, not a source-pinned promotion artifact.
A repeat with unchanged final sources is required.

The emitted next-gate wording predates the ingress correction: historical VC0
writes cannot directly fill the cluster. Canonical addressed K/V ejection must
be adapted into transposer target controls with complete backpressure checks.
The reported cycles are common-clock transport observations, not an independent
clock, CDC, physical PPA, activity-power, or full-workload frontier result.

Payload scope: the mesh testbench constructs VC1 beats with `make_canonical_beat`
and checks canonical root values. It imports measured cluster release cycles,
not the numerical output payloads of the cluster replay. The cluster exact-row
audit and mesh canonical-payload checks are separate compositional evidence;
their combination does not establish numerical end-to-end equivalence through
the complete producer, reducer, and mesh path.
