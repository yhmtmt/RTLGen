# Score32 HBM Controller Replay Integrated Frontier Ranking

This proposal dispatches the next score32 integrated frontier-ranking step after HBM controller replay has been merged.

The ranking should consume `decoder_attention_score32_hbm_controller_replay` as the score32 HBM/DRAM source row, while preserving the existing comparator stack and schedule-wrapper handling in non-replay variants.
