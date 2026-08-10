# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1`
- `title`: `Bounded Llama7B RMSNorm Phase-3 physical anchor`

## Why This Gate Is Required
- The physical request is only useful if the generated wrapper still matches the
  exact Phase-3 arithmetic and if the physical measurement is not misclassified
  as SRAM-backed storage evidence.

## Reference
- baseline_ref: `docs/proposals/prop_l1_decoder_llama7b_rmsnorm_phase3_v1/implementation_summary.md`
- reference_ref: `docs/reference/llama7b_rmsnorm_phase2_contract.md`

## Checks
- regenerated RTL equality:
  - threshold: checked `config.json` and `top.v` must match a fresh generator run
- wrapper contract:
  - threshold: top-level LANES=16 BF16 ready/valid ports, counters, and row/gamma register arrays present
- storage evidence classification:
  - threshold: no SRAM macro or macro-manifest implication in the generated wrapper
- lint:
  - threshold: Verilator `--lint-only -Wall -Wno-fatal` completes on the generated top and retains warnings in the job log

## Local Commands
- `python3 -m pytest tests/test_llama7b_rmsnorm_phase3.py -k "physical_guard"`
- `PYTHONPATH=control_plane python3 -m pytest control_plane/control_plane/tests/test_l1_task_generator.py -k "llama7b_rmsnorm_phase3"`

## Result
- status: passed
- note: Both targeted tests passed on 2026-08-10 UTC. No local OpenROAD run was performed.
