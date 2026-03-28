# Terminal int8 hard-sigmoid block

- item_id: `item_l1_terminal_hardsigmoid_block_v1`
- layer: `layer1`
- kind: `circuit`
- status: `merged`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-25T00:00:00Z`
- updated_utc: `2026-03-25T00:00:00Z`
- proposal_id: `prop_l1_terminal_hardsigmoid_block_v1`
- proposal_path: `docs/proposals/prop_l1_terminal_hardsigmoid_block_v1`
## Goal

Establish accepted physical metrics for one bounded `int8` terminal hard-sigmoid block using the existing integer `pwl` path.

## Why now

- it is the smallest next nonlinear block after accepted sigmoid and tanh wrappers
- it exercises the new automatic merge-to-finalization path on a real evaluation task
- it preserves the repo direction that lower-layer physical evidence is collected before broader architecture use
