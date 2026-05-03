# Implementation Summary

Implemented the bf16/PWL recovery proxy:

- added `score_tie_breaker=logit` support to the ONNX candidate runner
- added the `decoder_bf16_pwl_recovery_v1` rough grid
- added `summarize_llm_decoder_bf16_pwl_recovery.py`
- registered `decoder_bf16_pwl_recovery` in the Layer 2 task generator

Local validation:

- `python3 -m py_compile npu/eval/run_llm_decoder_onnx_candidate.py npu/eval/sweep_llm_decoder_candidate_quality.py npu/eval/summarize_llm_decoder_bf16_pwl_recovery.py control_plane/control_plane/services/l2_task_generator.py`
- `PYTHONPATH=/workspaces/RTLGen:/workspaces/RTLGen/control_plane /workspaces/RTLGen/control_plane/.venv/bin/python3 -m pytest -q tests/test_llm_decoder_bf16_pwl_recovery.py tests/test_llm_decoder_q8_norm_frontier.py control_plane/control_plane/tests/test_l2_task_generator.py`
- local recovery sweep produced `tie_break_recovery_sufficient`: baseline bf16/PWL was 46/48 next-token and 48/48 top-k; logit tie-break recovery was 48/48 next-token and 48/48 top-k.
