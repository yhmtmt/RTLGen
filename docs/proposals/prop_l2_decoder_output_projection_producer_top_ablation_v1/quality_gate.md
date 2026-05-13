# Quality Gate

The result is acceptable if:

- all variants use the nm2 producer base config
- full reference preserves `npu_top`
- the probe continues after failed variants
- each row includes static RTL counters
- timeout and stall classifications are preserved without retry loops

