# Score32 Schedule-Wrapper Integrated Frontier Ranking

This proposal queues the post-recost ranking step for the score32 exp-LUT Llama7B frontier.

It should run only after `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1` has merged. The ranking consumes that physical-feasibility artifact as the score32 row and reuses the existing HBM/DRAM service closure because the measured schedule-wrapper change does not alter token memory traffic.
