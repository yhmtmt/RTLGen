# Terminal int8 sigmoid real-seed variance block

- item_id: `item_l1_terminal_sigmoid_seedvariance_v2`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-04-06T13:40:00Z`
- updated_utc: `2026-04-06T13:40:00Z`
- proposal_id: `prop_l1_terminal_sigmoid_seedvariance_v2`
- proposal_path: `docs/proposals/prop_l1_terminal_sigmoid_seedvariance_v2`

## Problem
- the earlier seed-variance proof only recorded trial seeds in the control plane; it did not actually perturb OpenROAD

## Candidate Idea
- rerun the same sigmoid PWL block under five distinct `FLOW_RANDOM_SEED` values after wiring the seed into DPL, GRT, and DRT

## Why It Might Matter
- gives the first real measurement of seed-driven timing spread in this control plane
- establishes whether this small block is deterministic or still has optimization room under OpenROAD randomness

## Evaluation Sketch
- one proposal-backed L1 multi-trial sweep
- `trial_count = 5`
- fixed config and sweep, only seed changes

## Inputs / Sources
- `runs/designs/activations/terminal_sigmoid_int8_pwl_seedvariance2_wrapper/config_terminal_sigmoid_int8_pwl_seedvariance2.json`
- `runs/designs/activations/sweeps/nangate45_terminal_sigmoid_int8_pwl_v1.json`
- `docs/proposals/prop_l1_terminal_sigmoid_seedvariance_v1/proposal.json`
