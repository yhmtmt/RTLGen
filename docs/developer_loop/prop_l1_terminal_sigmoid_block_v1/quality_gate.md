# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_terminal_sigmoid_block_v1`
- `title`: `Terminal int8 sigmoid block`

## Why This Gate Is Required
- no separate model-quality gate is required at the circuit-only stage
- correctness gates move to local RTL or wrapper checks here, and to later
  Layer 2 output-quality comparison when the block is used in mapped models
- the first pass is intentionally limited to an `int8` block so correctness and
  physical characterization can be established before any `fp16` follow-on

## Reference
- baseline_ref: pending
- reference_ref: pending

## Checks
- local bounded-curve checks against the chosen `pwl` sigmoid points
- local RTL smoke check for wrapper integration and signed int8 saturation

## Local Commands
- `cmake -S /workspaces/RTLGen -B /tmp/rtlgen-build -G Ninja`
- `cmake --build /tmp/rtlgen-build --target rtlgen`
- `bash /workspaces/RTLGen/tests/test_activation_int.sh`
- `TMP=$(mktemp -d); cp /workspaces/RTLGen/examples/config_activation_sigmoid_int8.json "$TMP/config.json"; cd "$TMP"; /tmp/rtlgen-build/rtlgen config.json; iverilog -g2012 -s activation_sigmoid_int_tb -o sim sigmoid_int8_pwl.v /workspaces/RTLGen/tests/activation_sigmoid_int_tb.v; vvp sim`

## Result
- status: pass_local
- note: The bounded int8 sigmoid PWL path is implemented locally and passes RTL smoke checks; remote physical evaluation is the remaining gate.
