# Collected numerical leaf-to-mesh replay

The replay of all sixteen collected exact-cluster numerical streams passed.
All 512 finalized root rows matched the exact reference. The checker verified
8192 source handshakes and 79,396 arbitration decisions. Service completed at
cycle 73,845; historical VC0 traffic completed at cycle 7785, producing zero
VC0/VC1 overlap. There were 60,928 VC0 and 10,020 VC1 flits, with 64,172 recorded
contention cycles/events as defined by the testbench counter.

`measured_numerical_result.json` retains the observations, 52 source identities,
and three generated-file hashes. The runner verified that original and
generated sources remained unchanged through the replay. The input collection
is archived in the sibling exact-cluster-release-cadence proposal as
`all_cluster_numerical_payloads.json`; its compact serialization was checked
content-identical to the original collector output referenced by the result.

This closes the collected arithmetic-stress leaf-to-mesh numerical replay for
four groups, not full canonical attention execution. The leaf values and
release times came from sixteen separate concrete cluster simulations, then
were causally replayed through the mesh. Live producer/mesh feedback was not
simulated as one physical composition. VC0 uses historical traffic rather than
the corrected paired canonical K/V ingress schedule. The stress fixture varies
query values with placement and is not the resident-query workload contract.
Mapped canonical tensors, full score-production composition, CDC, routed PPA,
and activity-backed power remain required before a new Pareto claim.
