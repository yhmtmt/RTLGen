# L2 score32 exp-LUT divider generation-quality gate

This proposal is an evidence-only check for the candidate
`score32_exp_lut_div:q8,k8,v8,s32,w16,exp_lut_div_bucket20`.

Decision target: if this candidate passes the bounded native-checkpoint generation gate,
the exp-LUT divider bridge can advance to composed PPA recost.
If it fails, keep the bridge as diagnostic and continue with other softmax/precision
recovery work before any composed-PPA recost.

Inputs: baseline `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3` and
`l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1`.
This run is non-physical (`run_physical: false`) and requires merged inputs/materialized refs.
