# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_model_native_quality_7b_v1`
- `title`: `Evaluate 7B-class native KV quantization quality`

## Scope
- Added generator support in PR #927 for the
  `decoder_attention_kv_model_native_quality_7b` abstraction layer.
- Staged a remote-only L2 work item that runs the existing native KV
  quantization evaluator on a 7B-class checkpoint.
- Did not modify RTL, PPA sweeps, or prior TinyLlama native quality/recovery
  evidence.

## Files Changed
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`
- `docs/proposals/prop_l2_decoder_attention_kv_model_native_quality_7b_v1/*`

## Local Validation
- `PYTHONPATH=.:control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -k "model_native_quality"`
- result: passed

## Evaluation Request
- requested remote task: `l2_decoder_attention_kv_model_native_quality_7b_v1`
- cost class: medium/high depending on evaluator model cache
- default model: `mistralai/Mistral-7B-v0.1`
- evaluator overrides:
  - `RTLGEN_MODEL_NATIVE_7B_MODEL_ID`
  - `RTLGEN_MODEL_NATIVE_7B_EXPECTED_GQA_GROUP_SIZE`

## Risks
- Default Mistral-7B is 7B-class native GQA but not exact Llama7B/GQA8.
- Exact LLaMA-family checkpoints may be gated and require evaluator-local
  credentials.
- The run remains a teacher-forced prompt gate, not full perplexity or task
  accuracy.
