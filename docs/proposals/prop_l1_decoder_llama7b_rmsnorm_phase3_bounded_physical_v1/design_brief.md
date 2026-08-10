# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1`
- `title`: `Bounded Llama7B RMSNorm Phase-3 physical anchor`

## Problem
- The arithmetic and ready/valid behavior of Phase-3 RMSNorm are now real RTL, but
  the Llama7B architecture stack still lacks a measured Layer-1 physical anchor
  for that block.
- The merged generator uses large inferred row/gamma register arrays, so the
  first physical run needs a conservative boundary and an explicit caveat about
  what is and is not being measured.

## Hypothesis
- A single LANES=16 Nangate45 wrapper with contract regeneration, lint, and a
  conservative clock sweep should yield usable timing and area evidence without
  needing local OpenROAD or a broad parameter sweep.

## Evaluation Scope
- direct comparison set:
  - `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1`
- evaluation modes:
  - `physical_calibration` for one bounded Layer-1 sweep
- dependency order:
  - no prior DB items; dispatch only after merge
  - requires merged inputs and materialized refs
- excluded first-stage comparisons:
  - lane-count scaling
  - SRAM-backed storage substitutions
  - activity-backed energy
- follow-on broad sweep:
  - extend to alternative lane counts or storage replacements only if the LANES=16
    anchor is physically useful

## Knowledge Inputs
- `docs/reference/llama7b_rmsnorm_bf16_contract.md`
- `docs/reference/llama7b_rmsnorm_phase2_contract.md`
- `docs/proposals/prop_l1_decoder_llama7b_rmsnorm_phase3_v1/implementation_summary.md`

## Candidate Direction
- Reuse the merged `gen_llama7b_rmsnorm.py` generator through a dedicated
  `runs/designs/npu_blocks/...` physical wrapper package and a narrow
  `l1_task_generator` specialization that emits:
  - RTL generation
  - contract guard
  - Verilator lint
  - OpenROAD block sweep
  - timing summary extraction

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-08-10T00:00:00Z
- note: Narrow physical anchor only. No local OpenROAD and no DB insertion.

