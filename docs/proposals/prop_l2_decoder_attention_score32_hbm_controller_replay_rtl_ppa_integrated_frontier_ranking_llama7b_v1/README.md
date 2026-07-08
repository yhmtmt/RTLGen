# Score32 HBM Replay Controller RTL-PPA Integrated Frontier Ranking

This proposal queues the post-controller-PPA ranking step for the score32 Llama7B frontier.

It should run after `l1_decoder_attention_hbm_replay_controller_ppa_v1` has merged. The ranking consumes the existing deterministic HBM replay result and adds the measured Nangate45 RTL PPA evidence for the replay controller control path. It does not claim vendor HBM PHY or DRAM current-signoff closure.
