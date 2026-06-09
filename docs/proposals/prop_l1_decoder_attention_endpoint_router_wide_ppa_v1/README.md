# Wide Endpoint/Router/FIFO PPA

This proposal measures the wide on-chip primitive anchors required by the
current Llama7B attention frontier:

- `l1_onchip_endpoint_w1024_b4_eq16_bq16_wrapper`
- `l1_noc_router_p4_w2048_wrapper`
- `l1_noc_fifo_w2048_d16_wrapper`

These are the concrete PPA points identified by the endpoint/router/SRAM
composition audit before the on-chip service result can be treated as closed.
