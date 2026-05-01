# Decoder q8/bf16 Normalization Broad Distribution v2

- `proposal_id`: `prop_l2_decoder_q8_norm_distribution_broad_v2`
- `item_id`: `l2_decoder_q8_norm_distribution_broad_v2`
- abstraction: `decoder_q8_normalization_distribution_broad_v2`

The r4 distribution robustness job proved that the q8/bf16 normalization
frontier can run with measured q8 exact, q8 reciprocal, and bf16 reciprocal PPA
inputs. It did not prove distribution robustness: the dataset had 12 curated
samples.

This step expands the rough distribution to 48 samples across factual,
commonsense, arithmetic, sequence, code-like, dialogue, punctuation, long-context,
repetition, ambiguous, instruction, and symbolic categories. The goal is still
outline mapping, not final model-quality proof.

Expected output:

- `decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json`
- `decoder_q8_norm_frontier__l2_decoder_q8_norm_distribution_broad_v2.json`
- `decoder_q8_norm_frontier__l2_decoder_q8_norm_distribution_broad_v2.md`
