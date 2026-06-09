# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_v1`
- `title`: `Endpoint router SRAM composition audit for Llama7B frontier`

## Why This Gate Is Required
- The selected frontier uses a 128-byte endpoint packet and 2048-bit link, but current primitive metrics include narrower endpoint/router/FIFO wrappers.
- The exploration should explicitly separate physically backed values from lane-scaled estimates.

## Checks
- metric: source artifacts
  - threshold: command consumes endpoint ready-valid, endpoint full on-chip, and SRAM metrics artifacts
- metric: width closure
  - threshold: report includes endpoint, router, and FIFO width closure flags
- metric: SRAM closure
  - threshold: report distinguishes tile-local SRAM buffer coverage from full local-capacity SRAM closure
- metric: HBM/DRAM
  - threshold: report states HBM/DRAM service is inherited unchanged

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
