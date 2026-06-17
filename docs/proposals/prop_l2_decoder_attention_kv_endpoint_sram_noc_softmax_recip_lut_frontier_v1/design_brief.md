# Llama7B Endpoint SRAM/NoC Softmax Recip-LUT Frontier

## Purpose

Remove the current q10-only softmax local-cost assumption from the endpoint
SRAM/NoC full-search Llama7B frontier.

## Boundary

The current Llama7B local-cost file models one measured full-value datapath, one
standalone softmax-weight generator, one FIFO, one router, and one endpoint per
cluster. The merged composed reciprocal-LUT PPA result is useful frontier
evidence, but it covers a wider composed datapath boundary. This proposal first
measures q8 under the standalone softmax-weight boundary, then lets the L2
frontier compare q8/q10/q12 consistently.

## Execution Order

1. Run `l1_decoder_attention_softmax_weight_generator_q8_v1`.
2. Merge the q8 metrics artifact.
3. Run `l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1`.

The L2 job builds a temporary q8/q10/q12 local-cost profile file from committed
metrics before running the full-search scheduler.
