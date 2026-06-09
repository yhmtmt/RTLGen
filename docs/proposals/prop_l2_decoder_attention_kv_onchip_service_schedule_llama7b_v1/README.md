# Llama7B On-Chip SRAM/NoC Service Schedule

This proposal queues the next non-HBM L2 scheduler run after the practical
SRAM/NoC constrained frontier. The job consumes the retained frontier rows from
`l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2` and
refines only on-chip behavior:

- SRAM bank arbitration policy
- endpoint injection/ejection queue depth
- bank queue depth
- router/link hop latency
- packet payload size
- static wave, staggered wave, and prefetch-overlap scheduling

HBM/DRAM service is intentionally inherited unchanged from the input row. This
job is meant to identify which on-chip service policy should be embodied next
with RTL or a more detailed simulator.
