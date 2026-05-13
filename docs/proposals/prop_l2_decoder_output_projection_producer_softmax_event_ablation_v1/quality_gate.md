# Quality Gate

The result is acceptable if:

- all variants use the nm2 producer base config
- default `cq_mem_ablation_mode=full` preserves the existing full CQ RTL path
- the probe continues after failed variants
- each row includes static RTL counters
- timeout and stall classifications are preserved without retry loops
- the result compares against the prior CQ ablation that identified `cq_v1_softmax_event_only` as the first non-OK slice
