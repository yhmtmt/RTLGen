# Quality Gate

The result is acceptable if:

- `cq_v1_event_wait_only` no longer times out under the bounded nm2 synth-only probe
- `cq_v1_event_only` and `cq_v1_softmax_event_guard` record bounded results or a new clearly classified non-EVENT_WAIT failure
- `cq_v1_event_index_only` remains the direct dynamic-index diagnostic reference
- static RTL counters are included for every variant
- perf-vs-RTL event-DMA ordering remains equivalent
