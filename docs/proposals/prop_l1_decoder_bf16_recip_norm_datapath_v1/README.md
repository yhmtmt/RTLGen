# Decoder bf16 Reciprocal Normalization Datapath

This proposal records the Layer 1 measurement for the standalone row-wise bf16
reciprocal-normalization datapath added to RTLGen in PR #300.

The measurement closes the remaining bf16 normalization hardware gap called out
by the decoder quantization outline. It is intentionally a circuit-block PPA
measurement, not a full decoder promotion: it measures the packed-bf16
conversion, sum, reciprocal LUT, multiply, clamp, and bf16 output-conversion
path for `row_elems=8` on Nangate45.

The key accepted result is `l1_decoder_bf16_recip_norm_datapath_v1_r2`.
