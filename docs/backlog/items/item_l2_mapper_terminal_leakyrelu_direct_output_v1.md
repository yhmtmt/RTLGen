# Terminal LeakyReLU direct output

- item_id: `item_l2_mapper_terminal_leakyrelu_direct_output_v1`
- layer: `layer2`
- kind: `mapper`
- status: `promoted_to_proposal`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-27T06:30:00Z`
- updated_utc: `2026-03-27T06:30:00Z`
- proposal_id: `prop_l2_mapper_terminal_leakyrelu_direct_output_v1`
- proposal_path: `docs/proposals/prop_l2_mapper_terminal_leakyrelu_direct_output_v1`
## Summary
- extend the bounded terminal vec-op direct-output path to terminal `LeakyReLU` on fixed `nm1`
- stage the work as a merged `measurement_only` baseline first, then a paired fused comparison

## Dependencies
- accepted lower-layer source: `prop_l1_npu_nm1_leakyrelu_vec_enable_v1`

## First Remote Item
- `l2_prop_l2_mapper_terminal_leakyrelu_direct_output_v1_nm1_measurement_r1`
