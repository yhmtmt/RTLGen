# Design Brief

- `proposal_id`: `prop_l1_terminal_hardswish_block_v1`
- `title`: `Terminal int8 HardSwish block`

## Scope

- bounded `int8` HardSwish only
- existing integer `pwl` implementation path only
- one wrapper config and one Nangate45 sweep only

## Constraints

- keep the first pass small and saturating
- do not expand to integrated `nm1` or mapper work in this step
- use the same small-wrapper floorplan policy that already worked for nearby standalone activations
