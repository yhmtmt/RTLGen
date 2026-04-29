# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_llm_practical_decoder_proxy_v1`
- `title`: `LLM practical decoder proxy`

## Why This Gate Is Required
The proposal adds benchmark inputs and a campaign scaffold used for architecture
planning. The quality gate checks that the new model set is repo-portable,
path-valid, and runnable through the mapper/perf flow before remote evaluation.

## Reference
- proposal: `docs/proposals/prop_l2_llm_practical_decoder_proxy_v1/proposal.json`
- campaign: `runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json`
- model set: `runs/models/llm_practical_v1/manifest.json`

## Checks
- generator syntax:
  - threshold: `python3 -m py_compile` passes
- campaign path validation:
  - threshold: `npu/eval/validate.py --check_paths` passes
- mapper/perf smoke:
  - threshold: one local `run_campaign.py` sample lowers the first practical
    model and emits a perf trace
- largest-shape smoke:
  - threshold: the largest `kv512` six-block model lowers and emits a perf
    trace without SRAM-fit failure
- run index validation:
  - threshold: `scripts/validate_runs.py --skip_eval_queue` passes
- evaluator packaging:
  - threshold: generated review package resolves
    `docs/proposals/prop_l2_llm_practical_decoder_proxy_v1/proposal.json`

## Local Commands
- `python3 -m py_compile npu/mapper/examples/gen_llm_practical_suite_lite.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json --check_paths`
- `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json --repeat 1 --max_models 1 --max_arch 1 --modes flat_nomacro --jobs 1 --batch_id local_practical_smoke`
- `python3 npu/mapper/onnx_to_schedule.py --onnx runs/models/llm_practical_v1/practical_tail_attn6_s32_h64_kv512.onnx --arch npu/arch/examples/minimal.yml --out /tmp/rtlgen-practical-largest/schedule.yml --gemm-num-modules 1`
- `python3 npu/mapper/run.py /tmp/rtlgen-practical-largest/schedule.yml --out-bin /tmp/rtlgen-practical-largest/descriptors.bin`
- `python3 npu/sim/perf/run.py --bin /tmp/rtlgen-practical-largest/descriptors.bin --out /tmp/rtlgen-practical-largest/trace.json --overlap --config npu/sim/perf/example_config_fp16_cpp.json --gemm-engine-count 1 --summary`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: local-pass
- note: local syntax, path, run-index, one-sample campaign smoke, and largest
  model mapper/perf smoke checks passed; remote campaign execution remains
  pending.
