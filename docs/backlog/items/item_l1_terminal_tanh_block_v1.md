# Terminal int8 tanh block

- item_id: `item_l1_terminal_tanh_block_v1`
- layer: `layer1`
- kind: `circuit`
- status: `merged`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-24T12:00:00Z`
- updated_utc: `2026-03-24T12:01:06Z`
- proposal_id: `prop_l1_terminal_tanh_block_v1`
- proposal_path: `docs/proposals/prop_l1_terminal_tanh_block_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_activation_family_v1`
- triggering_evidence:
  - `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/analysis_report.md`
  - `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/promotion_decision.json`
  - `docs/proposals/prop_l1_terminal_sigmoid_block_v1/promotion_result.json`
  - `docs/proposals/prop_l1_npu_nm1_sigmoid_vec_enable_v1/promotion_result.json`

## Problem
- the bounded terminal activation-family work is now accepted for `Sigmoid`, but the next nonlinear family still has no lower-layer physical grounding
- broadening Layer 2 nonlinear activation support without a real Layer 1 `tanh` block would repeat the same under-grounded evaluation problem we had before sigmoid

## Candidate Idea
- implement the next bounded nonlinear terminal activation block: `int8 tanh`
- reuse the existing integer `pwl` path in `src/rtlgen` for a first-pass symmetric signed-domain approximation
- keep the first pass tightly bounded to one block and one physical sweep before any integrated or Layer 2 follow-on

## Why It Might Matter
- gives the next activation-family expansion a real physical source instead of relying on sigmoid-only grounding
- tests whether the same bounded `pwl` strategy extends to a second nonlinear family without immediately reopening broad architecture questions
- creates the prerequisite for a later integrated `nm1` `tanh` enable item and then a bounded Layer 2 `tanh` direct-output campaign

## Required Work
- l1 change: yes
- l2 change: not in this proposal
- mapper change: no in this proposal
- quality gate required: no separate model-quality gate for the circuit itself; output-quality gating belongs to the later Layer 2 use of the block

## Evaluation Sketch
- local:
  - define the bounded `int8 tanh` block and wrapper contract
  - add local RTL/smoke checks
- remote:
  - first-stage Layer 1 physical sweep on one bounded tanh block family
  - accept `metrics.csv` evidence and physical implementation outputs
- follow-on:
  - seed an integrated `nm1` tanh-enable architecture-block item
  - only then reopen bounded Layer 2 terminal `tanh` direct-output evaluation

## Inputs / Sources
- `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/analysis_report.md`
- `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/promotion_decision.json`
- `docs/proposals/prop_l1_terminal_sigmoid_block_v1/proposal.json`
- discussion on 2026-03-24 about returning to lower-layer grounding before extending nonlinear activation evaluation beyond sigmoid

## Open Questions
- which bounded `int8` tanh `pwl` point set is the smallest useful first pass
- whether the existing signed-domain `pwl` emission is sufficient as-is or needs a small symmetry-oriented cleanup
- what acceptance threshold is sufficient before the integrated `nm1` follow-on consumes this block

## Promotion Rule
- promote when the proposal names one bounded tanh block path, keeps the remote evaluation focused on physical implementation evidence, and explicitly defers integrated `nm1` and Layer 2 follow-ons until that evidence exists

## Outcome
- accepted physical evidence: PR `#80` / item `l1_prop_l1_terminal_tanh_block_v1_nangate45_r1`
- accepted best point:
  - `param_hash`: `23010967`
  - `critical_path_ns`: `0.1899`
  - `die_area`: `25600.0`
  - `total_power_mw`: `0.000111`
- follow-on: seed integrated `nm1` tanh-enable architecture-block work
