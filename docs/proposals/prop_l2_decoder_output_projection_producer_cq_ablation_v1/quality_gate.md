# Quality Gate

The result is acceptable if:

- all variants use the nm2 producer base config
- default `cq_mem_ablation_mode=full` preserves the existing full CQ RTL path
- the probe continues after failed variants
- each row includes static RTL counters
- timeout and stall classifications are preserved without retry loops
- the result compares against the prior top-level ablation that identified CQ memory/decode as the broad culprit
