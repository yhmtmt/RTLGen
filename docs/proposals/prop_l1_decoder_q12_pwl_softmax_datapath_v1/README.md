# q12 PWL Softmax Datapath

Proposal workspace for `prop_l1_decoder_q12_pwl_softmax_datapath_v1`.

This proposal promotes the q12 PWL decoder softmax survivor into a hardware
datapath calibration point. It measures the row-wise PWL-exp plus exact
normalization block in RTLGen/OpenROAD before making cost claims against q8
shift-exp or reciprocal-normalization alternatives.
