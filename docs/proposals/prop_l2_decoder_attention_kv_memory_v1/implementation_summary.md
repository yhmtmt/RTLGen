# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_memory_v1`
- title: Decoder attention/KV memory hierarchy breakdown

## Scope
- added a low-cost analytical attention/KV memory hierarchy estimator
- added a control-plane `decoder_attention_kv_memory` abstraction hook
- added proposal documentation and gates for `l2_decoder_attention_kv_memory_v1`
- did not add RTL, mapper changes, SRAM macro banking, or NoC arbitration RTL

## Files Changed
- `npu/eval/estimate_llm_decoder_attention_kv_memory.py`
- `tests/test_llm_decoder_attention_kv_memory.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`
- `docs/proposals/prop_l2_decoder_attention_kv_memory_v1/`

## Local Validation
- `python3 -m py_compile npu/eval/estimate_llm_decoder_attention_kv_memory.py control_plane/control_plane/services/l2_task_generator.py`
- `./control_plane/.venv/bin/python -m pytest -q tests/test_llm_decoder_attention_kv_memory.py tests/test_llm_decoder_stage_breakdown.py control_plane/control_plane/tests/test_l2_task_generator.py::test_generate_l2_campaign_task_adds_decoder_stage_breakdown_evidence control_plane/control_plane/tests/test_l2_task_generator.py::test_generate_l2_campaign_task_adds_decoder_attention_kv_memory_evidence`
- local estimator smoke wrote JSON and markdown outputs under `/tmp`

## Evaluation Request
- requested item: `l2_decoder_attention_kv_memory_v1`
- cost class: low
- baseline context: `l2_decoder_stage_breakdown_v1`

## Risks
- memory-tier bandwidths are planning values, not measured macros
- NoC effect is an effective bandwidth bound, not arbitration RTL
- quality effects of KV precision and MHA/GQA/MQA are out of scope
