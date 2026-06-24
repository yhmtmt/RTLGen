# NPU Evaluation Contract (System-Level)

## Purpose
This directory defines the contract for end-to-end NPU evaluation campaigns:
- ONNX model mapping inputs
- physical mapping (OpenROAD) outputs
- performance simulation outputs
- merged PPA + model-level metrics rows
- benchmark/model-set provenance (`model_set_id`, ONNX SHA256)

It is the first step toward a reproducible closed-loop flow:
`ONNX -> mapper -> physical -> perf -> report`.

## Files
- `npu/eval/contract.md`: human-readable contract and field definitions.
- `npu/eval/campaign.schema.json`: JSON schema for campaign manifests.
- `npu/eval/result_row.schema.json`: JSON schema for merged result rows.
- `npu/eval/llm_decoder_contract.schema.json`: JSON schema for the tiny
  decoder prompt/reference/candidate/metrics contract.
- `npu/eval/validate.py`: lightweight validator for campaign/result JSON.
- `npu/eval/validate_llm_decoder_contract.py`: lightweight validator for the
  checked-in decoder dataset, frozen artifacts, SHA256s, and token metrics.
- `npu/eval/examples/`: minimal examples.
- `runs/models/<model_set_id>/manifest.json`: shared benchmark model-set
  manifest with ONNX SHA256 checksums.
- `npu/eval/decoder_backend.py`: pluggable decoder backend interface for decoder-quality evaluation (`placeholder_v1`, frozen-artifact `replay_v1`, and external `command_json_v1`).
- `npu/eval/gen_llm_decoder_reference_suite.py`: generate reference-only
  decoder fixtures for the tiny decoder-quality stage.
- `npu/eval/gen_llm_decoder_candidate_suite.py`: generate candidate decoder
  fixtures for the tiny decoder-quality stage.
- `npu/eval/compare_llm_decoder_quality.py`: summarize token-level exact-match
  and top-k containment rates from decoder reference/candidate manifests.
- `npu/eval/sweep_llm_decoder_candidate_quality.py`: generate alternate
  candidate fixtures from decoder backend templates and summarize each
  candidate's token-level quality without changing the active candidate
  manifest.
- `npu/eval/run_llm_decoder_onnx_reference.py`: active exact-reference runner
  behind `command_json_v1` for the pinned tiny decoder ONNX export.
- `npu/eval/materialize_hf_decoder_contract.py`: evaluator-side materializer
  for larger Hugging Face causal decoders such as `distilgpt2`. It writes the
  decoder model/tokenizer contracts expected by the existing harness while
  leaving large generated artifacts under gitignored paths.
- `npu/eval/run_hf_decoder_materializer.sh`: control-plane entry point for the
  materializer. It selects an evaluator Python with `torch`, `transformers`, and
  `onnx`, preferring `RTLGEN_HF_MATERIALIZER_PYTHON`, then the AutoTuner env,
  then `python3`, and reports dependency failures before running the export.

The repo can now express a future exact-reference pair explicitly even before the
assets are present: the model contract may point at a `reference_onnx_binding.json`
that locks the intended ONNX path, tokenizer bundle, runtime, and fetch-plan
provenance. The current active first exact-reference source is `onnx-community/tiny-random-gpt2-ONNX` at commit `90f61e71d6fa8e571d0ab0f95a637a5d7d8ed52f`, paired with the GPT-2 tokenizer assets fetched from the same source. The active candidate side now uses the same contract with explicit softmax and normalization controls, and the current approximation mode is `onnx_logits_fp_softmax_approx_pwl_in_q4_w_q4_norm_recip_q10_prob_fp`. Both reference and candidate artifacts also trace `present.*` KV-cache tensors from the ONNX export, and the candidate side q4-quantizes those traced activations for internal-tensor comparison. The canonical tensor-summary helpers live in `npu/eval/tensor_trace_summary.py`; future RTL emitters should target `TENSOR_TRACE name=<id> step=<n> shape=<comma_dims> dtype=<dtype> min=<v> max=<v> mean=<v> std=<v>` lines, with optional quoted JSON `quantization='<object>'`, so Verilog and software traces hash through the same `selected_tensors_sha256` path.

The decoder-quality scaffold also introduces separate non-ONNX contracts for:
- datasets: `runs/datasets/...`
- tokenizers: `runs/tokenizers/...`
- placeholder decoder model bindings: `runs/models/<model_id>/model_contract.json`

For larger trained-checkpoint confirmation, run the materializer before any
reference/candidate generation:

```sh
python3 npu/eval/materialize_hf_decoder_contract.py \
  --model-id distilgpt2 \
  --contract-id llm_decoder_distilgpt2_trained_v1 \
  --dataset-dir runs/datasets/llm_decoder_eval_distilgpt2_trained_v1 \
  --sample-file runs/datasets/llm_decoder_eval_distilgpt2_trained_v1/samples.jsonl
```

The same materialized model/tokenizer can be reused for a separate stress
dataset by passing a different dataset id, dataset directory, and sample file:

```sh
python3 npu/eval/materialize_hf_decoder_contract.py \
  --model-id distilgpt2 \
  --contract-id llm_decoder_distilgpt2_trained_v1 \
  --dataset-id llm_decoder_eval_distilgpt2_prompt_stress_v1 \
  --dataset-dir runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1 \
  --sample-file runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1/samples.jsonl
```

The materializer requires `torch`, `transformers`, and `onnx` in the evaluator
Python environment. Generated files under
`runs/models/llm_decoder_distilgpt2_trained_v1/` and
`runs/tokenizers/llm_decoder_distilgpt2_trained_v1/` are intentionally ignored
and should not be committed by evaluator PRs.

Control-plane workers usually run commands from the control-plane venv, which
has `onnxruntime` for decoder inference but may not have the Hugging Face export
stack. L2 distilgpt2 jobs therefore invoke `run_hf_decoder_materializer.sh` for
the materialization step. Set `RTLGEN_HF_MATERIALIZER_PYTHON` in the evaluator
daemon environment when a host uses a non-default export environment; otherwise
the wrapper tries `/orfs/tools/AutoTuner/autotuner_env/bin/python3` and then
`python3`. Later reference/candidate commands still use normal `python3` for
ONNX Runtime inference.

Native-checkpoint quality jobs that run Hugging Face models directly should use
`run_hf_eval_python.sh` for the same interpreter selection without requiring the
`onnx` export dependency. The native GQA KV feedback runner supports a recovery
screen for KV4 scale granularity:

```sh
bash npu/eval/run_hf_eval_python.sh \
  npu/eval/evaluate_llm_decoder_model_native_kv_quant.py \
  --kv-bits-list 4 \
  --kv-granularity-list tensor,kv_head,token_vector \
  --out /tmp/native_kv_recovery.json \
  --out-md /tmp/native_kv_recovery.md
```

Treat a recovered non-tensor granularity as a hardware metadata/scale-cost
question, not as QAT evidence. If no granularity recovers top-1/top-k ranking,
the next quality path is true QAT/fine-tuning or the KV8 fallback.

## Validation
Validate campaign manifest:
```sh
python3 npu/eval/validate.py --campaign npu/eval/examples/minimal_campaign.json
```

Validate merged result row:
```sh
python3 npu/eval/validate.py --result-row npu/eval/examples/minimal_result_row.json
```

Validate the tiny decoder accuracy-stage contract:
```sh
python3 npu/eval/validate_llm_decoder_contract.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json
```

Run a bounded decoder candidate-quality sweep:
```sh
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json \
  --template candidate_onnx_softmax_exact \
  --template candidate_onnx_softmax_approx \
  --out-dir /tmp/decoder_candidate_sweep \
  --out /tmp/decoder_candidate_sweep.json
```

Run a rough decoder probability sensitivity grid:
```sh
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json \
  --rough-grid decoder_probability_broad_v1 \
  --out-dir /tmp/decoder_probability_broad_grid \
  --out /tmp/decoder_probability_broad_grid.json
```

Run a rough decoder floating-point format sensitivity grid:
```sh
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json \
  --rough-grid decoder_probability_fp_formats_v1 \
  --out-dir /tmp/decoder_probability_fp_grid \
  --out /tmp/decoder_probability_fp_grid.json
```

The fp-format grid is intentionally separate from the integer/fixed-point grid:
it probes fp16, bf16, and fp8-style dynamic range at logits, softmax
intermediates, reciprocal normalization, and final probabilities. Treat its
quality numbers as distribution-dependent evidence for the pinned tiny decoder
setup, not as final hardware-format acceptance.

Run the broader prompt-regime distribution robustness grid:
```sh
python3 npu/eval/gen_llm_decoder_reference_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json \
  --out-dir /tmp/decoder_distribution_reference_v1 \
  --out-manifest /tmp/decoder_distribution_reference_v1_manifest.json
python3 npu/eval/gen_llm_decoder_candidate_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json \
  --out-dir /tmp/decoder_distribution_candidate_v1 \
  --out-manifest /tmp/decoder_distribution_candidate_v1_manifest.json
jq '.reference_manifest="/tmp/decoder_distribution_reference_v1_manifest.json" |
    .candidate_manifest="/tmp/decoder_distribution_candidate_v1_manifest.json"' \
  runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json \
  > /tmp/manifest_distribution_v1.json
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest /tmp/manifest_distribution_v1.json \
  --rough-grid decoder_distribution_robustness_v1 \
  --out-dir /tmp/decoder_distribution_sweep \
  --out /tmp/decoder_distribution_sweep.json
```

The distribution grid records entropy, effective-vocabulary, score-sum, and
top-1/top-2 margin rollups alongside rank metrics. Use it to select follow-up
approximation families, not to make a general model-quality claim.

Run the expanded q8/bf16 normalization broad distribution check:
```sh
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json \
  --rough-grid decoder_q8_normalization_frontier_v1 \
  --out-dir /tmp/decoder_q8_norm_distribution_v2 \
  --out /tmp/decoder_q8_norm_distribution_v2.json
python3 npu/eval/estimate_llm_decoder_q8_norm_frontier.py \
  --sweep /tmp/decoder_q8_norm_distribution_v2.json \
  --q8-recip-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json \
  --q8-exact-ppa control_plane/shadow_exports/l1_promotions/l1_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_nangate45_r1.json \
  --bf16-recip-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json \
  --out /tmp/decoder_q8_norm_frontier_v2.json \
  --out-md /tmp/decoder_q8_norm_frontier_v2.md
```

This v2 check broadens the rough prompt categories before making a q8 reciprocal
versus bf16 reciprocal normalization decision. It remains tied to the pinned
tiny decoder model.

Diagnose the shared broad-v2 PWL exact-token misses:
```sh
python3 npu/eval/diagnose_llm_decoder_pwl_failures.py \
  --sweep runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json \
  --sample-file runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl \
  --out /tmp/decoder_pwl_failure_diagnosis.json \
  --out-md /tmp/decoder_pwl_failure_diagnosis.md
```

The diagnosis compares the exact softmax row against bf16 PWL, q8 PWL exact
normalization, and q8 PWL reciprocal q10 rows. Use it to decide whether the next
frontier job should target shared PWL/logit-margin sensitivity or normalization
precision.

Run the focused PWL/logit sensitivity ladder on the broad-v2 shared misses:
```sh
python3 npu/eval/gen_llm_decoder_reference_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_pwl_failure_focus_v1.json \
  --out-dir /tmp/reference_pwl_failure_focus_v1 \
  --out-manifest /tmp/reference_pwl_failure_focus_v1_manifest.json
python3 npu/eval/gen_llm_decoder_candidate_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_pwl_failure_focus_v1.json \
  --out-dir /tmp/candidate_pwl_failure_focus_v1 \
  --out-manifest /tmp/candidate_pwl_failure_focus_v1_manifest.json
jq '.reference_manifest="/tmp/reference_pwl_failure_focus_v1_manifest.json" |
    .candidate_manifest="/tmp/candidate_pwl_failure_focus_v1_manifest.json"' \
  runs/datasets/llm_decoder_eval_tiny_v1/manifest_pwl_failure_focus_v1.json \
  > /tmp/manifest_pwl_failure_focus_v1.json
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest /tmp/manifest_pwl_failure_focus_v1.json \
  --rough-grid decoder_pwl_logit_sensitivity_ladder_v1 \
  --out-dir /tmp/decoder_pwl_logit_ladder_sweep \
  --out /tmp/decoder_pwl_logit_ladder_sweep.json
python3 npu/eval/summarize_llm_decoder_pwl_logit_ladder.py \
  --sweep /tmp/decoder_pwl_logit_ladder_sweep.json \
  --sample-file runs/datasets/llm_decoder_eval_tiny_v1/samples_pwl_failure_focus_v1.jsonl \
  --out /tmp/decoder_pwl_logit_ladder.json \
  --out-md /tmp/decoder_pwl_logit_ladder.md
```

This ladder keeps the two failing broad-v2 samples and nearby arithmetic/list
controls together. It separates exact-softmax logit quantization, unquantized
PWL, PWL input/weight precision, and normalization precision.

Run the broad distribution check for the PWL survivor rows:
```sh
python3 npu/eval/gen_llm_decoder_reference_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json \
  --out-dir /tmp/reference_distribution_v2 \
  --out-manifest /tmp/reference_distribution_v2_manifest.json
python3 npu/eval/gen_llm_decoder_candidate_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json \
  --out-dir /tmp/candidate_distribution_v2 \
  --out-manifest /tmp/candidate_distribution_v2_manifest.json
jq '.reference_manifest="/tmp/reference_distribution_v2_manifest.json" |
    .candidate_manifest="/tmp/candidate_distribution_v2_manifest.json"' \
  runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json \
  > /tmp/manifest_distribution_v2.json
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest /tmp/manifest_distribution_v2.json \
  --rough-grid decoder_pwl_survivor_distribution_v1 \
  --out-dir /tmp/decoder_pwl_survivor_distribution_sweep \
  --out /tmp/decoder_pwl_survivor_distribution_sweep.json
python3 npu/eval/summarize_llm_decoder_pwl_survivor_distribution.py \
  --sweep /tmp/decoder_pwl_survivor_distribution_sweep.json \
  --sample-file runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl \
  --out /tmp/decoder_pwl_survivor_distribution.json \
  --out-md /tmp/decoder_pwl_survivor_distribution.md
```

This grid promotes the focused q12/unquantized PWL recovery to the expanded v2
prompt distribution and keeps q10/q8/bf16 rows as precision controls. Passing
this check is quality evidence for a later RTL/PPA calibration, not hardware
acceptance by itself.

Run the focused survivor prompt-stress grid:
```sh
python3 npu/eval/gen_llm_decoder_reference_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_prompt_stress_v1.json \
  --out-dir /tmp/decoder_prompt_stress_reference_v1 \
  --out-manifest /tmp/decoder_prompt_stress_reference_v1_manifest.json
python3 npu/eval/gen_llm_decoder_candidate_suite.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_prompt_stress_v1.json \
  --out-dir /tmp/decoder_prompt_stress_candidate_v1 \
  --out-manifest /tmp/decoder_prompt_stress_candidate_v1_manifest.json
jq '.reference_manifest="/tmp/decoder_prompt_stress_reference_v1_manifest.json" |
    .candidate_manifest="/tmp/decoder_prompt_stress_candidate_v1_manifest.json"' \
  runs/datasets/llm_decoder_eval_tiny_v1/manifest_prompt_stress_v1.json \
  > /tmp/manifest_prompt_stress_v1.json
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest /tmp/manifest_prompt_stress_v1.json \
  --rough-grid decoder_survivor_prompt_stress_v1 \
  --out-dir /tmp/decoder_prompt_stress_sweep \
  --out /tmp/decoder_prompt_stress_sweep.json
```

The prompt-stress grid excludes the already-collapsed fixed probability q8 and
fp8_e4m3 paths. It is intended to confirm survivor robustness before narrower
hardware-cost work.

Rank prompt-stress survivors with a rough implementation-cost proxy:
```sh
python3 npu/eval/estimate_llm_decoder_survivor_cost.py \
  --sweep runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json \
  --out /tmp/decoder_survivor_cost_proxy.json \
  --out-md /tmp/decoder_survivor_cost_proxy.md
```

The cost proxy gates rows on exact prompt-stress quality and then scores rough
softmax/probability-path terms. Treat it as a planning rank for the next RTL or
OpenROAD step, not as measured PPA.

The decoder cost proxy and the later PWL/q8-normalization detail scores are
hand-written planning heuristics. They are not derived from a paper and they do
not independently balance performance, power, and area. Their role is to choose
which exact-safe architecture point should be physically calibrated next. Use
RTLGen/OpenROAD Layer 1 evidence, such as
`prop_l1_decoder_normalization_arithmetic_calibration_v1`, before making a
hardware acceptance claim.

Break down the exact-safe PWL frontier after the survivor cost proxy:
```sh
python3 npu/eval/estimate_llm_decoder_pwl_frontier.py \
  --sweep runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json \
  --cost-proxy runs/datasets/llm_decoder_eval_tiny_v1/decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.json \
  --out /tmp/decoder_pwl_frontier_detail.json \
  --out-md /tmp/decoder_pwl_frontier_detail.md
```

The frontier detail report compares only `grid_approx_pwl_bf16_path` and
`grid_approx_pwl_in_q8_w_q8_norm_exact`. It separates PWL table footprint,
interpolation datapath width, normalization path, and integration risk so the
next hardware-cost job can target the blocker instead of sweeping approximation
parameters blindly.

Run the focused q8 PWL normalization frontier:
```sh
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_prompt_stress_v1.json \
  --rough-grid decoder_q8_normalization_frontier_v1 \
  --out-dir /tmp/decoder_q8_norm_frontier_sweep \
  --out /tmp/decoder_q8_norm_frontier_sweep.json
python3 npu/eval/estimate_llm_decoder_q8_norm_frontier.py \
  --sweep /tmp/decoder_q8_norm_frontier_sweep.json \
  --q8-recip-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json \
  --bf16-recip-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json \
  --bf16-tie-rank-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json \
  --bf16-recovery runs/datasets/llm_decoder_eval_tiny_v1/decoder_bf16_pwl_recovery__l2_decoder_bf16_pwl_recovery_v1.json \
  --out /tmp/decoder_q8_norm_frontier.json \
  --out-md /tmp/decoder_q8_norm_frontier.md
```

This frontier tests q8 PWL exact normalization against q8 PWL quantized
reciprocal normalization at q10/q12/q14/q16, with the bf16 reciprocal PWL row
kept as the current anchor. A reciprocal row is only a candidate if it preserves
the full prompt-stress next-token and top-k gate. When the merged q8 reciprocal
datapath artifact is available, q10/q12/q14/q16 are ranked by measured
Nangate45 critical path, then area, then power. When the merged bf16 reciprocal
datapath artifact is available, the bf16 anchor is ranked with the same measured
metric ordering. When a bf16 tie-break recovery artifact and score tie-rank PPA
artifact are both available, the recovered bf16 row is ranked with an explicit
additive component model: bf16 reciprocal normalization plus score tie-rank.
q8 exact normalization uses the measured row-wise int8 softmax baseline when
that artifact is available.

Run the bf16/PWL scale-proxy recovery screen:
```sh
python3 npu/eval/sweep_llm_decoder_candidate_quality.py \
  --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_scale_proxy_v1.json \
  --rough-grid decoder_bf16_pwl_scale_probe_v1 \
  --out-dir /tmp/decoder_bf16_pwl_scale_probe \
  --out /tmp/decoder_bf16_pwl_scale_probe.json
python3 npu/eval/summarize_llm_decoder_bf16_pwl_recovery.py \
  --sweep /tmp/decoder_bf16_pwl_scale_probe.json \
  --out /tmp/decoder_bf16_pwl_scale_probe_summary.json \
  --out-md /tmp/decoder_bf16_pwl_scale_probe_summary.md
```

This screen keeps the same tiny ONNX decoder but raises rank pressure by
requesting top-16 over the full 50k-token vocabulary and broadens prompt
categories to include longer contexts, denser code/symbolic prompts, repeated
patterns, and low-margin continuations. It answers whether the bf16/PWL plus
logit tie-break behavior survives a rough scale proxy before spending evaluator
time on a larger imported model or an integrated decoder datapath.

Run the GPT-2 raw-logit rank-bypass summary with measured rank PPA:
```sh
python3 npu/eval/summarize_llm_decoder_logit_rank_bypass.py \
  --sweep runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_quality_sweep__l2_decoder_gpt2_logit_rank_bypass_v1.json \
  --rank-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json \
  --out /tmp/decoder_gpt2_logit_rank_bypass.json \
  --out-md /tmp/decoder_gpt2_logit_rank_bypass.md
```

This summary uses the merged row-8 Nangate45 logit-only rank datapath instead
of the older bf16 score/tie-rank proxy. The k=1 row is the current greedy
argmax cost anchor, while the k=4 row is the current top-k/beam ranking anchor.
Sampling and probability-reporting modes remain outside this bypass because
they need calibrated probabilities, not only rank order.

Run the decoder logit-rank streaming hierarchy estimate with the explicit
macro-boundary diagnostic as sensitivity evidence:
```sh
python3 npu/eval/estimate_llm_decoder_logit_rank_streaming_hierarchy.py \
  --rank-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json \
  --scale-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json \
  --candidate-merge-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json \
  --boundary-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json \
  --out /tmp/decoder_logit_rank_streaming.json \
  --out-md /tmp/decoder_logit_rank_streaming.md
```

The boundary PPA is reported separately from normal ranker PPA. Use it to track
how exposed scalar-pin macro assumptions affect wide `r128/k1` timing and
perimeter feasibility; do not charge its padded die area to a producer-integrated
ranker unless explicitly modelling a standalone exposed-pin macro.

After the corresponding Layer 1 multiplier and accumulator/adder calibration
jobs merge, synthesize the measured primitive evidence into a decoder
normalization report:
```sh
python3 npu/eval/calibrate_llm_decoder_normalization_cost.py \
  --out /tmp/decoder_norm_ppa_calibration.json \
  --out-md /tmp/decoder_norm_ppa_calibration.md
```

The calibration report keeps `critical_path_ns`, `die_area`, and
`total_power_mw` as separate Nangate45 axes. It filters out rows from other
platforms before composing decoder-normalization evidence, marks the q8 exact
divider and bf16 reciprocal/multiply paths as unmeasured gaps, and records that
q10/q12/q14/q16 share the same current 16-bit multiplier plus accumulator
primitive envelope. Under that envelope, the physical primitive metrics do not
make q10 cheaper than q12/q14/q16; q10 remains a quality/minimum-precision
choice until an integrated datapath measurement says otherwise.

## Mixed-Int8 Quality-Backed Frontier
After running native 7B-class attention-shadow quality gates, do not rank a
mixed/int8 energy row by PPA alone. Reconcile the latest energy closure with the
latest broad native quality artifact first:
```sh
python3 npu/eval/audit_llm_decoder_attention_mixed_int8_quality_backed_frontier.py \
  --mixed-int8-energy-closure-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_energy_closure__l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2.json \
  --mixed-int8-broad-native-quality-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json \
  --out /tmp/decoder_attention_mixed_int8_quality_backed_frontier.json \
  --out-md /tmp/decoder_attention_mixed_int8_quality_backed_frontier.md
```

If the broad quality gate only passes `qkv8_float_exact`, prior score/softmax
quantized energy rows such as `s8/w8/recip_lut` are unranked latency/traffic
floors, not quality-backed frontier points. The next PPA job must recost the
q8/k8/v8 projection path with matching high-precision or exact score-softmax
hardware before comparing token throughput, energy, and area against the FP16
baseline.

Optionally verify path-like fields exist:
```sh
python3 npu/eval/validate.py --campaign <campaign.json> --check_paths
```

If the referenced model manifest uses external fetch metadata, materialize the
ONNX files first:
```sh
python3 npu/eval/fetch_models.py --manifest runs/models/<model_set_id>/manifest.json
```
Then rerun `--check_paths`.

Reuse-oriented campaign example:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json \
  --check_paths
```

## Campaign Runner (Phase-2 Scaffold)
Run mapper + perf and merge with physical metrics into append-only results CSV:
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
If a model file declared in the manifest is missing locally, the runner now
fails early with a fetch hint instead of falling through to mapper errors.
The runner honors optional per-architecture `physical_select` filters in the
campaign (`compare_group`, `tag_prefix`) and encodes physical `param_hash` into
`run_id` as stable design-point identity across sweep variants.
Each emitted row also includes `sample_id`/`batch_id`/`sample_index` so
statistical reruns can coexist without overloading `run_id`.
Row `notes` include mapper split metadata keys for quick filtering:
`mapper_split_enabled`, `mapper_split_chunk_count`, `mapper_split_chunks`.
Each campaign must also declare `model_set_id` and `model_manifest`
(`runs/models/<set>/manifest.json`), and emitted rows include
`model_set_id`/`model_manifest`/`onnx_sha256` for traceability.
Use a distinct campaign per benchmark set revision (do not silently mutate
model membership inside one campaign ID).
Model manifests may keep large ONNX binaries out of the repo by attaching an
optional `fetch` object to each model entry. The fetch tool materializes the
file into `onnx_path` while preserving the existing `onnx_sha256` provenance
contract.
When `architecture_points[].layer1_modules` is set, campaign validation checks
selected candidate IDs against `runs/candidates/...` manifests and rejects
`wrapped_io` candidates unless `allow_wrapped_io=true` is explicitly set.
It reuses existing per-model mapper/perf artifacts under
`<campaign_dir>/artifacts/` when input metadata matches; force full rerun with
`--no_reuse_model_artifacts`.
Use `--jobs <N>` to parallelize model-level mapper/perf generation when running
multiple models in one campaign.
Use `--batch_id <label>` to tag rerun batches explicitly (optional).
Use campaign field `physical_source_campaign` to record which prior campaign
provided baseline physical settings/results context for reuse runs.

If physical rows are missing in `<design_dir>/metrics.csv`, allow runner to
invoke the sweep:
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --run_physical
```

Dry-run (print commands only):
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --dry_run
```

## Campaign Reporting
Generate per-model summaries and aggregate ranking from merged CSV:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
The report step also emits:
- `summary.csv` (all model + aggregate summaries)
- `pareto.csv` (non-dominated aggregate points by latency/energy/runtime)
- `best_point.json` (weighted-objective best point)

Optional objective weights:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --w_latency 1.0 --w_energy 1.0 --w_runtime 0.2
```

## Objective Profile Sweep
Run multiple objective profiles and collect best-point recommendations:
```sh
python3 npu/eval/optimize_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --profiles_json runs/campaigns/npu/e2e_eval_v0/objective_profiles.json
```
Outputs:
- `objective_sweep.csv`
- `objective_sweep.md`
- per-profile reports under `objective_profiles/<profile>/`

## Decoder Attention/KV Physical HBM Model
`estimate_llm_decoder_attention_kv_physical_hbm_frontier.py` is the planning
model for long-context KV-cache service. It derives HBM bytes/cycle from stack
count, pseudo-channel count, interface width, transfer rate, and core clock,
then combines that with shared-SRAM residency, bank service, NoC service, tile
size, and prefetch depth.

The scalar memory, NoC, MAC throughput, and vector throughput options also
accept comma-separated sweeps. This keeps quality-backed jobs from ranking
unsafe KV4/MQA points while still testing how the optimum moves with die size,
memory hierarchy assumptions, and compute array sizing:

```sh
python3 npu/eval/estimate_llm_decoder_attention_kv_physical_hbm_frontier.py \
  --sequence-length-list 131072 \
  --kv-sharing-list gqa8 \
  --kv-bits-list 8,16 \
  --sram-area-fraction 0.4,0.6,0.75 \
  --noc-bandwidth-bytes-per-cycle 8192,32768 \
  --noc-hops 1,4 \
  --macs-per-cycle 32768,65536,131072,262144,524288 \
  --vector-ops-per-cycle 8192,16384,32768,65536 \
  --out /tmp/kv.json --out-md /tmp/kv.md
```

Treat high SRAM fractions and very large die points as planning bounds until
they are backed by SRAM macro/floorplan data.
For large sweeps, the JSON retains all global top rows and the 200 lowest
latency grouped memory/NoC rows; the full generated row count is still recorded
in `sweep_summary`.
