# Score32 Exact Hierarchy Cadence Audit

- decision: `score32_schedule_wrapper_cadence_arithmetically_reproducible_but_exact_hierarchy_unclosed`
- source recost: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json`
- subtile pipeline: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_llama7b_v1.json`
- wrapper config: `runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/config.json`
- wrapper metrics: `runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv`
- exact c16 config: `runs/designs/npu_blocks/attention_score32_exact_partial_producer_tree_c16_r2_l8_b59/config.json`

## Reproduced Frontier Arithmetic

| metric | value |
| --- | ---: |
| seq | 131072 |
| tile tokens | 1024 |
| tile count | 128 |
| active global clusters | 16 |
| tile waves | 8 |
| wrapper total MAC/cycle | 256 |
| wrapper-cluster datapath MAC/cycle | 128 |
| wrapper count | 428 |
| wrapper-cluster datapaths | 856 |
| frontier MAC/cycle | 109568 |

Eight global clusters carry `54` datapaths and eight carry `53`.
The conservative per-cluster capacity is `53 x 128 = 6784` MAC/cycle.

Each tile does `1024 x 4096 = 4194304` QK MACs and the same value MACs, so each barrier stage takes `ceil(4194304/6784) = 619` cycles.

## 986-Cycle Reconstruction

- subtiles: `8`
- qk/value per subtile: `78` / `78` cycles
- stats per subtile: `15` cycles
- HBM per subtile: `163` cycles
- aux memory release per subtile: `86` cycles
- prefetch distance: `3`
- reconstructed pipeline cycles: `986`

| subtile | hbm_ready | aux_release | qk_start | qk_done | stats_done | value_start | value_done |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 78 | 93 | 93 | 171 |
| 1 | 0 | 86 | 86 | 164 | 179 | 179 | 257 |
| 2 | 0 | 172 | 172 | 250 | 265 | 265 | 343 |
| 3 | 163 | 258 | 258 | 336 | 351 | 351 | 429 |
| 4 | 326 | 344 | 344 | 422 | 437 | 437 | 515 |
| 5 | 489 | 430 | 489 | 567 | 582 | 582 | 660 |
| 6 | 652 | 516 | 652 | 730 | 745 | 745 | 823 |
| 7 | 815 | 602 | 815 | 893 | 908 | 908 | 986 |

## Exact Hierarchy Gap

- merged native c16 exact slice: `128` MAC/cycle (`16 x m1x8` producers)
- frontier ratio: `856x` below the `109568`-MAC/cycle frontier
- placeholder config max_blocks: `16`
- tokens per exact block: `8`
- placeholder blocks per 1024-token tile: `128`
- placeholder blocks per head for one-command eight-wave persistence: `1024`
- local merges per beat: `840`
- global merges per beat: `15`

The current c16 placeholder is therefore not enough: it is too small in MAC density and its `max_blocks=16` only diagnoses the placeholder path, not the required producer contract.

In the required hierarchy, a `53`-datapath cluster spreads `128` tile blocks across `106` streams, so `22` streams carry `2` blocks and `84` carry `1`. A `54`-datapath cluster spreads them across `108` streams, so `20` streams carry `2` blocks and `88` carry `1`.
That fixes per-wave producer demand at `2` blocks/stream, and the checked-in generator floor `max_blocks >= 8` is already sufficient.

## Wrapper Classification

- The measured dual-stream wrapper is a structural PPA anchor, not a functional exact-partial producer.
- Its generator uses deterministic seed/stream-buffer stimulus and exposes PPA outputs directly.
- It supports density estimates, but it does not establish functional equivalence or exact partial-state cadence.

## Next L1 Contract

- proposal: `prop_l1_decoder_attention_score32_exact_partial_dual_stream_producer_v1`
- required block: `functional_2stream_m8x8_exact_partial_producer_before_53_54_way_local_aggregation`
- producer streams: `2`
- per-wave blocks per tile: `128`
- max blocks per stream per wave: `2`
- minimum supported producer `max_blocks`: `8`
- temporal accumulation boundary: per-wave producer emission, local 53/54-way reduction, then persistent local aggregate state across 8 waves before one c16 global exact reduction

## Non-Claims

- Do not revise frontier throughput or latency yet.
- The 986-cycle tile service point is arithmetically reproducible from checked-in sources, but hardware-equivalence closure remains open.
- The native c16 exact slice proves protocol semantics only; it does not validate the 109568-MAC/cycle frontier cadence.
- The next unmeasured block is the local 53/54-way reducer plus temporal exact-partial state across 8 waves.
