# Item: Terminal ReLU6 Direct Output

## Summary
- extend the bounded terminal vec-op direct-output path to terminal `ReLU6` on fixed `nm1`
- stage the work as a merged `measurement_only` baseline first, then a paired fused comparison

## Dependencies
- accepted lower-layer source: `prop_l1_npu_nm1_relu6_vec_enable_v1`

## First Remote Item
- `l2_prop_l2_mapper_terminal_relu6_direct_output_v1_nm1_measurement_r1`
