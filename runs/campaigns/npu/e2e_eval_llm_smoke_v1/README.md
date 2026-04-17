# NPU E2E Evaluation Campaign: `llm_smoke_v1`

This is the first runnable LLM-oriented smoke campaign.

What it does:
- uses model-set identity `llm_smoke_v1`,
- exercises the new attention-proxy non-terminal `Softmax` lowering path,
- keeps architecture scope narrow to existing `fp16_nm1` and `fp16_nm2` points.

Manifest:
- `runs/campaigns/npu/e2e_eval_llm_smoke_v1/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_llm_smoke_v1/campaign.json \
  --check_paths
```

Notes:
- This campaign is a bring-up stage for scheduler visibility and repeated-softmax flow.
- It is not yet an LLM-accuracy campaign. Approximation/precision evaluation must be added in a later benchmark stage with numerical reference checking.
