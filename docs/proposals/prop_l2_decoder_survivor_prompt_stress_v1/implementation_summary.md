# Implementation Summary

- Added `decoder_survivor_prompt_stress_v1` to the decoder rough-grid sweep.
- Added `decoder_survivor_prompt_stress` evidence generation to the L2 task
  generator.
- Added `samples_prompt_stress_v1.jsonl` and `manifest_prompt_stress_v1.json`
  for the focused 24-row prompt-stress set.

## Verification

- `python3 -m py_compile npu/eval/sweep_llm_decoder_candidate_quality.py control_plane/control_plane/services/l2_task_generator.py`
- `PYTHONPATH=control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -q`
- prompt-stress manifest smoke:
  - generate reference/candidate manifests
  - validate the prompt-stress contract
  - run `--rough-grid decoder_survivor_prompt_stress_v1`
