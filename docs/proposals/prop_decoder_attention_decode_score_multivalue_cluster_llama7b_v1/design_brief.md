# Shared-Score Multivalue Cluster

The current local-cluster frontier bound is useful evidence, but it prices an
architecture that fills and stores the M1x8 score row 16 times per 8-token
block because each value-slice pass owns its own score path.

This follow-on cluster changes that boundary:

1. Fill one M1x8 score row once per 8-token block.
2. Store the scores once in shared score state.
3. Replay 16 eight-dimensional value slices from that shared score state into
   the full 128 output dimensions.
4. Stream eight-dimensional result beats and reuse one iterative divider.

The semantic contract does not change: signed-int8 Q/K/V, signed-32 scores, and
LUT softmax must still match the existing integer decode model before any PPA
job runs.

This proposal explicitly revises `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2`
as an architecture bound only. Its JSON/Markdown evidence remains valid and
must stay committed; the new multivalue path simply replaces that repeated-fill
bound with a stricter shared-score candidate once the new equivalence and PPA
steps land.
