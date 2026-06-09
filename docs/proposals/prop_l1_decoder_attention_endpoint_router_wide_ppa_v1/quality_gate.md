# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_attention_endpoint_router_wide_ppa_v1`
- `title`: `Measure wide endpoint/router/FIFO PPA anchors for Llama7B attention frontier`

## Checks
- metric: endpoint width
  - threshold: measure `l1_onchip_endpoint_w1024_b4_eq16_bq16_wrapper`
- metric: router width
  - threshold: measure `l1_noc_router_p4_w2048_wrapper`
- metric: FIFO width
  - threshold: measure `l1_noc_fifo_w2048_d16_wrapper`
- metric: scope
  - threshold: keep full local SRAM capacity and HBM/DRAM out of this L1 item

## Result
- status: pending
