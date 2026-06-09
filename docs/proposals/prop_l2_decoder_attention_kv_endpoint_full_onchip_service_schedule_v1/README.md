# Endpoint Full-Search On-Chip Service Schedule

This proposal applies the explicit on-chip service model to the current
cap-aware endpoint full-search Llama7B frontier.

The input is the finalized endpoint SRAM/NoC full-search schedule. The output
should report the best policy for SRAM bank arbitration, endpoint queues, bank
queues, packet payload, router hop latency, wave staggering, and prefetch
overlap while inheriting HBM/DRAM service unchanged.

