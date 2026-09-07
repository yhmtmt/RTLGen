# Verified local measured-release mesh replay

The unchanged-source full replay passed and reproduced the exploratory result.
The four tracked runner/preparer/testbench/test source SHA-256 values matched
at launch and completion; every report source reference was independently
verified against the committed files. The executable sources are those in
commit `fc1a7042` (subsequent closure-matrix documentation commit `f2ca8134`
does not change them). `local_verified_result.json` preserves the emitted report.

| Observation | Result |
|---|---:|
| VC0 completion | 7,785 cycles |
| VC1 and total service completion | 73,845 cycles |
| Eager capacity comparison | 15,769 cycles |
| Simultaneous VC0/VC1 valid cycles | 0 |
| Simultaneous VC0/VC1 arbitrated cycles | 0 |
| Source handshakes checked | 8,192 |
| Release arbitration decisions checked | 79,396 |
| Protocol errors | 0 |

The test checks 60,928 VC0 flits and 512 canonical exact VC1 rows. Cluster
release times drive one held beat per source with stall-dilated later releases;
the Python model agrees with the recorded source and arbitration traces.

This verifies common-clock transport for this test workload. The VC1 payloads
are canonical test values, not the measured numerical cluster outputs. VC0 is
the historical traffic fixture, not canonical K/V ingress. Therefore this is
not a complete numerical dataflow, independent-clock/CDC, activity-power,
routed PPA, or workload Pareto result. Connect canonical addressed K/V ingress
through transposer controls and propagate actual cluster numerical outputs
through the mesh before making those composition claims.

No remote evaluation was dispatched. The existing human dispatch gate remains
separate from this local evidence.
