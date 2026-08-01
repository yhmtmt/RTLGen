# Score32 Exact Partial Pair Merge Contract

The folded exact pair merge uses the canonical exact-partial numerical semantics
under the distinct
`score32_online_exact_partial_pair_merge_folded_sharedscale_v1` microarchitecture
profile.

Contracted implementation points:

- one shared signed `41x24` scale path is invoked per cycle
- one separately shared unsigned `33x24` scale path handles exp-sum scaling
- pair capture to the first output handshake opportunity is `20` cycles
- compute launch to the first output handshake opportunity is `19` cycles
- compute-launch interval without output backpressure is `20` cycles
- one prefetched left beat and one prefetched right beat may be buffered while the
  current pair is being merged

Cycle numbers refer to active-edge handshake observations. With continuously
valid inputs and continuously ready output, pair 0 is accepted at cycle `0`,
launched at cycle `1`, and can fire at cycle `20`. Pair 1 is prefetched at cycle
`2`, launches at cycle `21`, and can fire at cycle `40`. Output backpressure holds
the output payload stable and delays the next launch until one cycle after the
blocked output fires.

This block does not claim tree-level closure, direct-link closure, finalizer
closure, NoC closure, or SRAM closure.
