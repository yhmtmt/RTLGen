# Quality Gate

- The source sweep must be
  `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json`.
- Rows must be eligible for implementation-cost narrowing only when next-token
  and top-k both match all prompt-stress samples.
- The JSON and Markdown outputs must state that this is a relative proxy, not
  RTL/OpenROAD PPA.
- The ranked output must keep blocked/non-exact rows visible with miss lists.
- `scripts/validate_runs.py --skip_eval_queue` must pass before submission.
