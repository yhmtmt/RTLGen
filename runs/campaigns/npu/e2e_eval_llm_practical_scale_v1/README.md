# NPU E2E Evaluation Campaign: `llm_practical_scale_v1`

This campaign extends the practical decoder-style proxy from `llm_practical_v1`
to larger active-token batches and wider KV-context score dimensions.

What it does:
- uses model-set identity `llm_practical_scale_v1`;
- exercises 64 active tokens against 1024-2048 KV-context score dimensions;
- keeps the current physical architecture points, `fp16_nm1` and `fp16_nm2`;
- records whether larger LLM-like pressure changes scheduler visibility,
  softmax occupancy, or the `nm1` vs `nm2` PPA ranking.

Validate:

```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_llm_practical_scale_v1/campaign.json \
  --check_paths
```

Boundary:
- This is graph-level scheduler/PPA evidence only.
- Dataset-backed decoder quality remains under `llm_decoder_eval_tiny_v1`.
