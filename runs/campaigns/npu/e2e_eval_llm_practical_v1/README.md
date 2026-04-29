# NPU E2E Evaluation Campaign: `llm_practical_v1`

This is the first practical decoder-style proxy campaign after
`llm_attention_tail_stress_v1`.

What it does:
- uses model-set identity `llm_practical_v1`,
- exercises active-token batches against larger KV-context score dimensions,
- keeps the same two existing architecture points, `fp16_nm1` and `fp16_nm2`,
- records whether KV-context proxy pressure changes scheduler visibility before
  a softmax datapath proposal is opened.

Manifest:
- `runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json \
  --check_paths
```

Boundary:
- This is still a graph proxy and campaign-level scheduler/PPA stage.
- Dataset-backed decoder quality remains under `llm_decoder_eval_tiny_v1` and
  should be used before accepting approximation changes for LLM behavior.
