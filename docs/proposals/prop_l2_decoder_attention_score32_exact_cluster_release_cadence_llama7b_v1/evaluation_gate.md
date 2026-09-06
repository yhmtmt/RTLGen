# Human Evaluation Gate

This corrective cadence run is source-ready but must not be dispatched until a human explicitly approves it.

- pinned source commit: `1b639463ca3bfb4a811f4c857560d239bc4ca5d3`
- requested item: `l2_decoder_attention_score32_exact_cluster_release_cadence_llama7b_v1`
- execution class: non-physical promotion-scale RTL simulation
- dispatch status: `awaiting_human_approval`

Acceptance requires direct representative p54 and p53 cluster-wrapper replay with all four groups, eight persistent waves per group, 512 exact rows per representative, every accepted output cycle, structured row equality, zero protocol errors, and source hashes. Fine-grained component replay, inferred 986-cycle timing, eager release, or a black-box SRAM substitution is not equivalent evidence.

The evaluator must provide a working hierarchical Verilator launcher or another demonstrated backend capable of elaborating the direct hierarchy. The developer PC's packaged Verilator recursively references a missing launcher, while direct Icarus elaboration expands 48,384 dense score-SRAM instances and is not an accepted fallback.
