# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1`
- `title`: `Measure segmented/narrower NoC router/FIFO alternatives for Llama7B endpoint composition`

## Why This Gate Is Required
- The composition audit must not treat failed flat 2048-bit router/FIFO PPA as feasible. This gate provides bounded lane-level alternatives for the next composition model.

## Reference
- baseline_ref: `l1_decoder_attention_endpoint_router_wide_ppa_v1`
- reference_ref: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r3`

## Checks
- metric: generated metrics rows
  - threshold: status recorded for all four requested primitive wrappers at all sweep points.
- metric: boundary interpretation
  - threshold: flat 2048-bit router/FIFO are not retried as the selected closure path.

## Local Commands
- command: `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: pending
- note: Awaiting L1 sweep.
