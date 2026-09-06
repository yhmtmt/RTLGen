# Human Evaluation Gate

This corrective cadence run is source-ready but must not be dispatched until a human explicitly approves it.

- pinned source commit: `90047370adde8e174c72de0764fccc496ae5534d`
- requested item: `l2_decoder_attention_score32_exact_cluster_release_cadence_llama7b_v1`
- execution class: non-physical promotion-scale RTL simulation
- dispatch status: `awaiting_human_approval`

Acceptance requires direct representative p54 and p53 cluster-wrapper replay with all four groups, eight persistent waves per group, 512 exact rows per representative, every accepted output cycle, structured row equality, zero protocol errors, and source hashes. Fine-grained component replay, inferred 986-cycle timing, eager release, or a black-box SRAM substitution is not equivalent evidence.

The pinned probe uses a two-stage hierarchical Verilator flow and short lexical module-family aliases, eliminating the developer PC package's missing-launcher and double-underscore name-mangling failures. Its direct p54 child Verilation then reached a signal-9 local resource boundary. The evaluator must have sufficient memory for that direct hierarchy; direct Icarus elaboration expands 48,384 dense score-SRAM instances and is not an accepted fallback.
