# Score32 HBM Replay Controller RTL-PPA Recost

This proposal folds the merged c4 HBM replay-controller Nangate45 area, power, and critical path into the current score32 Llama7B frontier row.

It follows the evidence-only ranking in `prop_l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_integrated_frontier_ranking_llama7b_v1`. The recost keeps the fixed die area unchanged, adds controller area to the measured logic subtotal, adds controller active energy over token latency, and checks the measured controller critical path against the schedule clock.
