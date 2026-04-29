# q8 Reciprocal Normalization Datapath

Proposal workspace for `prop_l1_decoder_q8_recip_norm_datapath_v1`.

This proposal turns the q8 reciprocal-normalization frontier into an integrated
RTLGen/OpenROAD measurement. The previous calibration measured multiplier and
adder primitives only; this one measures divider-free row-wise int8 softmax
normalization blocks using a quantized reciprocal lookup and multiply path.
