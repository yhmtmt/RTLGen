# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_probability_sweep_v1`
- `title`: `LLM decoder probability-template sweep`

## Scope
- added `npu/eval/sweep_llm_decoder_candidate_quality.py`
- added `decoder_probability_sweep` evidence wiring in the L2 task generator
- added generator coverage for the new evidence hook
- documented the decoder-quality sweep path
- added proposal metadata for an evaluator-run sweep
- did not change RTL, mapper logic, simulator logic, tokenizer assets, prompt
  samples, or the active exact candidate manifest

## Files Changed
- `npu/eval/sweep_llm_decoder_candidate_quality.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`
- `npu/eval/README.md`
- `docs/architecture/llm_decoder_accuracy_stage_v1.md`
- `docs/proposals/prop_l2_decoder_probability_sweep_v1/`

## Local Validation
- `python3 -m py_compile npu/eval/sweep_llm_decoder_candidate_quality.py`
- `python3 npu/eval/sweep_llm_decoder_candidate_quality.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json --template candidate_onnx_softmax_exact --template candidate_onnx_softmax_approx --out-dir /tmp/decoder_candidate_sweep --out /tmp/decoder_candidate_sweep.json`
- `PYTHONPATH=control_plane python3 -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -q`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Evaluation Request
- item: `l2_decoder_probability_sweep_v1`
- task type: `l2_campaign`
- evaluation mode: `broad_ranking`
- abstraction layer: `decoder_probability_sweep`

## Risks
- The tiny prompt set remains a narrow quality gate.
- Sweep evidence is still software-emulated probability-path evidence.
