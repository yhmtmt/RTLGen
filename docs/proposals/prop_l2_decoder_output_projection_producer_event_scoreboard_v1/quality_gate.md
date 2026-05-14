# Quality Gate

The result is acceptable if:

- generated RTL for full and EVENT diagnostic modes contains no `event_state` vector
- perf-vs-RTL EVENT/DMA contract tests pass
- `cq_v1_event_wait_only` no longer times out under the bounded nm2 synth-only probe
- `cq_v1_event_only` and `cq_v1_softmax_event_guard` record bounded results or a new clearly classified non-scoreboard failure
- static RTL counters are included for every variant
