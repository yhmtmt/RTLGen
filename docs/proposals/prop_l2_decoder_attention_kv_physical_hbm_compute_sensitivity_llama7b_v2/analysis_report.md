# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- `candidate_id`: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`

## Evaluations Consumed
- work item id:
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- run key:
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2_run_ff3db632b8d9c8c8`
- source commit:
  `1454629818ddaffb32375c31115845dd85390350`

## Baseline Comparison
- baseline used:
  `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`
- the campaign reuses the measured local L1 physical costs and sweeps analytic
  compute throughput in the physical HBM/SRAM/NoC model.

## Result
- result: mixed, iterate
- confidence level: medium for planning, low for final physical architecture
- boundary: 32768 and 65536 MAC/cycle points remain `tile_attention` bound
  across the die sizes. At 400 and 800 mm2, 131072 MAC/cycle is the first swept
  point classified as HBM-bound. At 1200 mm2, 131072 MAC/cycle with only 8192
  vector ops/cycle is still tile-attention bound; 131072 MAC/cycle with 16384
  vector ops/cycle becomes HBM-bound.
- best selected 131k point: 800 mm2, native GQA8 KV8, 524288 MAC/cycle,
  65536 vector ops/cycle, 8 HBM stacks, 16 pseudo-channels per stack,
  9000 MT/s, 0.75 HBM efficiency, 2503.395 MiB SRAM, local SRAM fraction 0.25,
  HBM byte share 0.541615, 86.112 us latency, dominant resource `hbm`.
- practical implication: the currently small measured local compute point is
  not enough to claim the full Llama7B schedule is HBM-dominant. The next
  architecture work should map concrete clustered RTL near the 131k to 524k
  MAC/cycle range and vary NoC/SRAM assumptions.

## Failures and Caveats
- No evaluator command failed for this work item.
- The physical HBM and NoC model is analytic and does not include routed global
  NoC or HBM controller timing.
- The campaign wrapper still includes the reused MLP/NPU physical summary; the
  Llama7B conclusion is carried by the decoder attention/KV dataset artifacts.
- The compute-throughput values are not yet backed by concrete larger-array
  RTL/PPA.

## Recommendation
- iterate
- The job answers the immediate boundary question, but it should not be
  promoted as a final architecture. Use the boundary to launch concrete
  clustered compute and memory/NoC structure evaluations.
