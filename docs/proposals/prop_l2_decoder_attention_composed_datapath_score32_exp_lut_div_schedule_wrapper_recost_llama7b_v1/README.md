# Llama7B score32 exp-LUT schedule-wrapper recost

This proposal adds the L2 follow-on for the measured score32 exp-LUT
dual-stream schedule-wrapper PPA.

Item: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`

The recost consumes the bounded c2/c4 schedule-wrapper metrics and substitutes
them into the Llama7B area-fit replica model. This replaces the previous modeled
composition of separate datapath, command-dispatch, and local schedule overhead.
