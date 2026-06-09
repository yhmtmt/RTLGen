# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_local_sram_capacity_v1`
- `title`: `Local SRAM capacity profile for Llama7B attention frontier`

## Checks
- metric: source frontier
  - threshold: command consumes endpoint full on-chip schedule result
- metric: capacity
  - threshold: report includes local capacity bytes per cluster and allocated bytes per cluster
- metric: CACTI
  - threshold: report includes SRAM metrics summary and budget fit
- metric: scope
  - threshold: HBM/DRAM and endpoint/router/FIFO PPA remain out of scope

## Result
- status: pending
