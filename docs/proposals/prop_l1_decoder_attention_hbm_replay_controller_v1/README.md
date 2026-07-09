# Decoder Attention HBM Replay Controller PPA

This proposal measures the controller logic corresponding to the current score32 HBM replay parameters.

The result should replace the current "deterministic cycle-level, not RTL timing" abstraction with a Nangate45 measured control block before the next Llama7B frontier recost.

The first `l1_decoder_attention_hbm_replay_controller_ppa_v1` attempt completed all commands but failed acceptance because c8 and c16 produced `flow_failed` metrics rows. For this frontier-boundary measurement those rows are useful physical evidence, so the recovery request `l1_decoder_attention_hbm_replay_controller_ppa_v2` records both status=ok and non-ok rows instead of rejecting the run.
