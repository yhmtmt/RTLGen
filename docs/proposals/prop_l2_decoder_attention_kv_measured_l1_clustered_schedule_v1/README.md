# L2 Measured-L1 Clustered Attention Schedule

This proposal records the Llama7B 131k-context clustered attention schedule
after charging measured per-cluster L1 local costs.

The run used source commit `0a1e86e0bce5672d52eb4b831971c0858bc84fab` and
produced PR #722, merged as `30825fe1fd17bf9a2b84f00f7c90917cd38786f0`.

Primary evidence:

- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_l1_clustered_schedule__l2_decoder_attention_kv_measured_l1_clustered_schedule_v1.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_l1_clustered_schedule__l2_decoder_attention_kv_measured_l1_clustered_schedule_v1.md`
- `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_kv_measured_l1_clustered_schedule_v1__l2_decoder_attention_kv_measured_l1_clustered_schedule_v1/report.md`

Conclusion: iterate. The measured L1 charge did not overturn the broad
frontier; the best sampled point still uses `nm64_flat` compute with the
smallest measured local profile. The next useful work is to close the missing
full softmax-weighted value datapath and then replace the remaining abstract
NoC/SRAM schedule terms.
