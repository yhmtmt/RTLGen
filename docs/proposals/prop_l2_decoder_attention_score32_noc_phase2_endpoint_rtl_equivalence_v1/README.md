# Score32 Phase-2 Endpoint/RTL Equivalence

- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_v1`
- scope: replay the complete Llama7B Phase-2 packet schedule through finite SRAM endpoints and the exact 4x4 mesh RTL
- output: one JSON evidence file and one Markdown report

This closes the logical zero-copy release-queue shortcut. The paired scheduler
installs an RX context before releasing TX, obeys finite endpoint queues, and
compares cycle and router counters against an endpoint-aware performance model.
