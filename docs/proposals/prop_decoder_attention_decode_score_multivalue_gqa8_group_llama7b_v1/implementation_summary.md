# Implementation Summary

The generated wrapper instantiates eight existing shared-score multivalue
clusters. Command and input handshakes are accepted atomically. The 64-bit
query input carries one signed-int8 scalar for each query head, while one
64-bit key beat is broadcast to all children.

During value replay, the wrapper accepts an external request only when all
children present the same block address and value-slice index. One tagged
512-bit response is broadcast only when all children can accept it. Divergent
requests or response readiness set a sticky protocol error.

Results are exposed one child at a time in query-head order, with sixteen
eight-dimensional slices per head. The wrapper counts one accepted and one
completed GQA command, while child arithmetic and score storage remain the
already-equivalent measured cluster implementation.

The follow-on activity job consumes the merged group PPA and equivalence
artifacts. Its report must separate directly annotated routed activity from
any compositional scaling and keeps VCD, ODB, and SPEF evaluator-local. This
closes group-component energy only; memory, NoC, HBM/DRAM, and total-token
energy remain outside this measurement.
