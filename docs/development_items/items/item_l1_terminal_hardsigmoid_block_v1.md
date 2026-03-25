# item_l1_terminal_hardsigmoid_block_v1

- layer: `layer1`
- kind: `circuit_block`
- status: `active`

## Goal

Establish accepted physical metrics for one bounded `int8` terminal hard-sigmoid block using the existing integer `pwl` path.

## Why now

- it is the smallest next nonlinear block after accepted sigmoid and tanh wrappers
- it exercises the new automatic merge-to-finalization path on a real evaluation task
- it preserves the repo direction that lower-layer physical evidence is collected before broader architecture use
