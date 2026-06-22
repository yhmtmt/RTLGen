# Implementation Summary

## Scope
- Add the proposal scaffold for the L2 rerank job that replaces the PR #981
  corrected measured-compute frontier with merged V3 dense-GEMM compute rows.
- Add a distinct control-plane L2 abstraction layer that first regenerates
  measured-compute rows with `npu_dense_gemm_tile_v3_depth_hier`, then runs the
  measured-compute energy closure audit on that V3 artifact.

## Files Added
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/README.md`
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/proposal.json`
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/evaluation_requests.json`
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/evaluation_gate.md`
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/quality_gate.md`
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/design_brief.md`
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`

## Local Validation
- `python3 -m py_compile control_plane/control_plane/services/l2_task_generator.py`
- `PYTHONPATH=.:control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -k 'dense_gemm_v3_measured_compute_closure or measured_compute_energy_closure'`
- Status remains blocked until L1 V3 merge artifacts are available.
