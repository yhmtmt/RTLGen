# Local exact cluster cadence measurement

The developer-PC Verilator replay passed for both representative cluster
structures. `local_cadence_result.json` preserves all output cycles, exact-row
audits, successful build/run phases, and source/configuration SHA-256 identities.
Those identities were verified against the working sources before preserving
the artifact. This is local evidence, not a remotely dispatched evaluation.

Partitioning the producer, reducer, and SRAM endpoint into reusable hierarchical
children allowed both complete cluster wrappers to compile and simulate.

| Group | p54 first / last output cycle | p53 first / last output cycle |
|---:|---:|---:|
| 0 | 17432 / 17559 | 17437 / 17564 |
| 1 | 33824 / 33951 | 33829 / 33956 |
| 2 | 50216 / 50343 | 50221 / 50348 |
| 3 | 66608 / 66735 | 66613 / 66740 |

Each representative emitted 512 exact rows across four groups and 32 accepted
wave commands, with zero reported errors. Consecutive group starts are 16,392
cycles apart. These cycles belong to the generated cluster's single clock;
they do not establish an independent mesh clock rate or CDC implementation.

The first common-clock shared-mesh replay reached its final traffic checks at
cycle 76,449 but failed the unconditional overlap assertion: observed simultaneous
VC0/VC1 valid and arbitrated counts were both zero. The failure occurred after
the exact payload and traffic-total checks. This is diagnostic evidence only;
the corrected full replay must pass and its source/arbitration traces must agree
with the model before claiming shared-mesh verification.

The corrected assertion retains mandatory overlap in eager stress modes and
records overlap as an observation for measured release schedules. Physical PPA,
activity power, direct VC0 SRAM-to-cluster fill dependence, independent clocks,
and full-workload mapper closure remain outside this measurement. No Pareto
promotion follows from this artifact alone.
