# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_llm_practical_decoder_proxy_v1`
- `title`: `LLM practical decoder proxy`

## Scope
- added the `llm_practical_v1` ONNX-lite model generator
- generated three practical decoder-style proxy models
- added a Layer 2 campaign scaffold using existing `fp16_nm1` and `fp16_nm2`
  architecture points
- documented the benchmark-ladder transition from tail stress to practical
  decoder proxy evidence
- did not change RTL, mapper lowering logic, simulator logic, or scoring code

## Files Changed
- `npu/mapper/examples/gen_llm_practical_suite_lite.py`
- `runs/models/llm_practical_v1/`
- `runs/campaigns/npu/e2e_eval_llm_practical_v1/`
- `docs/proposals/prop_l2_llm_practical_decoder_proxy_v1/`
- `docs/architecture/llm_attention_benchmark_ladder.md`
- `docs/architecture/llm_decoder_accuracy_stage_v1.md`
- `docs/backlog/items/item_eval_llm_attention_suite_v1.md`
- `runs/models/README.md`
- `npu/mapper/README.md`

## Local Validation
- `python3 -m py_compile npu/mapper/examples/gen_llm_practical_suite_lite.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json --check_paths`
- `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json --repeat 1 --max_models 1 --max_arch 1 --modes flat_nomacro --jobs 1 --batch_id local_practical_smoke`
- `python3 npu/mapper/onnx_to_schedule.py --onnx runs/models/llm_practical_v1/practical_tail_attn6_s32_h64_kv512.onnx --arch npu/arch/examples/minimal.yml --out /tmp/rtlgen-practical-largest/schedule.yml --gemm-num-modules 1`
- `python3 npu/mapper/run.py /tmp/rtlgen-practical-largest/schedule.yml --out-bin /tmp/rtlgen-practical-largest/descriptors.bin`
- `python3 npu/sim/perf/run.py --bin /tmp/rtlgen-practical-largest/descriptors.bin --out /tmp/rtlgen-practical-largest/trace.json --overlap --config npu/sim/perf/example_config_fp16_cpp.json --gemm-engine-count 1 --summary`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Evaluation Request
- item: `l2_llm_practical_decoder_proxy_v1`
- task type: `l2_campaign`
- evaluation mode: `broad_ranking`
- platform: `nangate45`

## Risks
- This is still a graph proxy, not a dataset-backed decoder-quality benchmark.
- KV-context pressure is represented through `score_dim` and metadata rather
  than a true KV-cache memory subsystem.
