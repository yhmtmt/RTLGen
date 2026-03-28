# Design Brief

- `proposal_id`: `prop_l1_terminal_leakyrelu_block_v1`
- `title`: `Terminal int8 LeakyReLU block`

## Scope

- bounded `int8` leakyrelu only
- existing integer activation implementation path only
- one wrapper config and one Nangate45 sweep only

## Constraints

- keep the first pass small and saturating
- do not expand to integrated `nm1` or mapper work in this step
- use a conservative negative slope of `1/8` to keep the smoke semantics obvious
