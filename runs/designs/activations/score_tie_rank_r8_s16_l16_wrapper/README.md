# score_tie_rank_r8_s16_l16_wrapper

Layer 1 datapath proxy for decoder score ranking with a logit tie-break key.

The block selects the best lane from 8 unsigned 16-bit quantized scores. When
scores are exactly equal it selects the lane with the larger signed 16-bit logit
proxy. Exact score and logit ties keep the lowest lane index.
