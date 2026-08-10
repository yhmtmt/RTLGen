# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1`
- bounded Llama7B RMSNorm Phase-3 physical anchor

## Scope
- Added a dedicated Layer-1 bounded physical package for the merged Phase-3
  RMSNorm RTL.
- Added a narrow `l1_task_generator` specialization that emits generator,
  contract guard, Verilator lint, OpenROAD sweep, and timing-summary steps for a
  `top_name + llama7b_rmsnorm` design config.
- Added a physical guard that regenerates the wrapper and explicitly classifies
  the row/gamma storage arrays as inferred register storage rather than SRAM
  evidence.
- Did not run OpenROAD locally and did not create a DB item.

## Files Changed
- `control_plane/control_plane/services/l1_task_generator.py`
- `control_plane/control_plane/tests/test_l1_task_generator.py`
- `npu/eval/check_llama7b_rmsnorm_phase3_physical_guard.py`
- `tests/test_llama7b_rmsnorm_phase3.py`
- `runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/config.json`
- `runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/README.md`
- `runs/campaigns/npu/llama7b_rmsnorm_phase3_physical_v1/sweeps/nangate45_llama7b_rmsnorm_phase3_bounded_l16.json`
- `docs/proposals/prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1/*`

## Local Validation
- `python3 -m pytest tests/test_llama7b_rmsnorm_phase3.py -k "physical_guard"`: passed
- `PYTHONPATH=control_plane python3 -m pytest control_plane/control_plane/tests/test_l1_task_generator.py -k "llama7b_rmsnorm_phase3"`: passed

## Evaluation Request
- requested remote task:
  - `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1`
- cost class:
  - medium
- baseline to compare against:
  - merged Phase-3 implementation summary and Phase-2 numeric contract

## Risks
- Physical feasibility still depends on the large inferred register arrays.
- The first bounded run covers only LANES=16.
- Power remains generic OpenROAD power.
