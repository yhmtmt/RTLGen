# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_hbm_energy_calibration_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_hbm_energy_calibration_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_hbm_energy_calibration_llama7b_v1`
- `l2_decoder_attention_hbm_energy_calibration_llama7b_v1_run_75da55250a5254ab`
- source commit: `53584274bf7f29e3943ef9c0906a994694cb3908`
- review: PR #977

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `hbm_energy_calibration_preserves_energy_frontier`
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_calibration__l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json: decision=hbm_energy_calibration_preserves_energy_frontier; recommended_next_step=If HBM dominates under source-backed aggregate calibration, replace the aggregate pJ/bit bound with a stack-current/controller-calibrated HBM model before final energy ranking.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_calibration__l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json: decision=hbm_energy_calibration_preserves_energy_frontier; recommended_next_step=If HBM dominates under source-backed aggregate calibration, replace the aggregate pJ/bit bound with a stack-current/controller-calibrated HBM model before final energy ranking.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_calibration__l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json: decision=hbm_energy_calibration_preserves_energy_frontier; recommended_next_step=If HBM dominates under source-backed aggregate calibration, replace the aggregate pJ/bit bound with a stack-current/controller-calibrated HBM model before final energy ranking.
- next_action: inspect follow-on work after l2_decoder_attention_hbm_energy_calibration_llama7b_v1
