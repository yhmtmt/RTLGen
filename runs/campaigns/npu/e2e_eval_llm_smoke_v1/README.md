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
- Deterministic numerical reference fixtures for the same model binaries now live under:
  - `runs/models/llm_smoke_v1/reference_manifest.json`
- First candidate-output fixtures for the same binaries now also live under:
  - `runs/models/llm_smoke_v1/candidate_manifest.json`
- It is still not yet a full LLM-accuracy campaign: no dataset/training loop or realistic decoder-quality evaluation is wired in yet.
