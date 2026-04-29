# Implementation Summary

- Added distribution rollups to ONNX reference and candidate decoder runner
  artifacts.
- Added aggregate distribution rollups to decoder quality comparison and sweep
  outputs.
- Added `decoder_distribution_robustness_v1` to the decoder rough-grid sweep.
- Added `decoder_distribution_robustness` evidence generation to the L2 task
  generator.
- Added `samples_distribution_v1.jsonl` and `manifest_distribution_v1.json` for
  the broader rough prompt-regime set.

## Verification

- `python3 -m py_compile npu/eval/run_llm_decoder_onnx_reference.py npu/eval/run_llm_decoder_onnx_candidate.py npu/eval/compare_llm_decoder_quality.py npu/eval/sweep_llm_decoder_candidate_quality.py`
- `PYTHONPATH=control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest tests/test_llm_decoder_onnx_runner.py tests/test_llm_decoder_onnx_candidate_runner.py control_plane/control_plane/tests/test_l2_task_generator.py -q`
- distribution manifest smoke:
  - generate reference/candidate manifests
  - validate the distribution contract
  - run `--rough-grid decoder_distribution_robustness_v1`
