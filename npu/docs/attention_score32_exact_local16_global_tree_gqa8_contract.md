# Score32 Exact Local16 Global Tree GQA8 Contract

This block is the full structural exact wrapper that composes:

- sixteen corrected `gen_attention_score32_exact_local_temporal_reducer_gqa8.py` reducers
- exactly eight `p54` clusters and eight `p53` clusters
- the existing `gen_attention_score32_exact_banked_finalized_tree.py` `c16/r2/l8/b59` finalized exact tree

## Scope

- flat packed `856`-leaf exact-partial wrapper boundary
- per-leaf exact metadata:
  `command_id`, `head_id`, signed `global_max`, unsigned `exp_sum`, `slice`, `last`, and `8 x S41` numerators
- per-cluster GQA8 local exact aggregation across `8` heads, `16` slices, and `8` waves
- direct global exact merge/finalization through the existing ordered banked `c16/r2/l8/b59` tree
- finalized `320`-bit value output plus component/global counters and protocol signals

The producer-side score contract is Llama7B `head_dim=128`: each token block is
the dot product of `128` accepted signed INT8 query/key beats, with `input_last`
asserted only on the final dimension.

## Cluster Partition

- clusters `0..7` use `54` local producer leaves each
- clusters `8..15` use `53` local producer leaves each
- total local producer leaves: `856`
- flat wrapper leaf base indices:
  `[0, 54, 108, 162, 216, 270, 324, 378, 432, 485, 538, 591, 644, 697, 750, 803]`

## Interface Compatibility And Adaptation

- Wrapper top -> local reducers:
  direct flat packed exact-partial buses, partitioned only by the fixed cluster leaf bases above.
- Local reducer aggregate -> global finalized tree leaf:
  direct field-preserving mapping of `valid`, `ready`, `command_id`, `head_id`,
  `global_max`, `exp_sum`, `slice`, `last`, and `328`-bit value payload.
- Finalized tree root -> wrapper output:
  direct mapping of the existing finalized-tree `root_*` interface.
- Output semantic adaptation:
  none on the local-to-global exact-partial boundary; the only semantic change is
  the existing finalized-tree contract itself, which consumes `global_max` and
  `exp_sum` internally and emits finalized values only.

## Retracted One-Dimensional Evidence

The July 28, 2026 bounded run used this command:

- `python npu/eval/probe_attention_score32_exact_local16_global_tree_gqa8.py --config runs/designs/npu_blocks/attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59/config.json --timeout-sec 240 --json`

It recorded the following historical point:

- command groups: `1`
- head bases: `[0]`
- total local producer leaves: `856`
- cluster aggregate outputs: `2048`
- finalized outputs: `128`
- exact finalized hash:
  `a8e78a3e4c551fec6aeb050b92fc08d2ece9a32a06d21b2789bc1b19c5416821`
- first finalized output cycle: `3139`
- last finalized output cycle: `3266`
- integrated drain cycles: `3268`
- global dispatch stalls: `0`
- per-cluster local-root completed count: `1024`
- per-cluster temporal-merge completed count: `896`
- per-cluster emitted aggregate beats: `128`
- protocol errors: `0`

That result is not valid Llama7B full-head equivalence evidence. Its stimulus
asserted `input_last` on every producer beat, so every score covered one product
instead of the required `128`-term dot product. The structural wrapper and
reduction rows were exercised, but the sequential producer accumulation path was
not. The result and dependent full-GQA8 rerank must remain as retracted audit
history until replaced by reports that record:

- `head_dimension=128`
- `score_accumulation_beats_per_block=128`
- `producer_handshake_count=1,048,576` for one head group
- `producer_handshake_count=4,194,304` for four head groups
- exact structured cluster/root row equality and zero protocol errors

## Historical Heavier Run Status

The same full wrapper was also attempted as a heavier two-group run on July 28,
2026 with:

- `python npu/eval/probe_attention_score32_exact_local16_global_tree_gqa8.py --command-count 2 --head-bases 0,8 --timeout-sec 60 --json`

Outcome:

- status: `timeout`
- timeout bound: `60` seconds
- finalized outputs observed before timeout: `0`
- cluster aggregate outputs observed before timeout: `0`

The final RTL is retained unchanged. Structural wiring, submodule contracts, and
the staged Python reference remain proven independently of that heavier timeout.

## Remaining Abstractions

- Producer/NoC/SRAM closure remains open at the packed local exact-partial boundary.
- Physical PPA closure remains open for the full composed wrapper.
