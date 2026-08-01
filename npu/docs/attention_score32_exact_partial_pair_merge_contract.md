# Score32 Exact Partial Pair Merge Contract

The folded exact pair merge keeps the existing exact-partial stream semantics and
changes only the internal arithmetic schedule.

Contracted implementation points:

- one shared signed `41x24` scale path is invoked per cycle
- one separately shared unsigned `33x24` scale path handles exp-sum scaling
- pair capture to output-valid latency is `19` cycles
- compute-launch to output-valid latency is `18` cycles
- compute-launch interval without output backpressure is `20` cycles
- one prefetched left beat and one prefetched right beat may be buffered while the
  current pair is being merged

This block does not claim tree-level closure, direct-link closure, finalizer
closure, NoC closure, or SRAM closure.
