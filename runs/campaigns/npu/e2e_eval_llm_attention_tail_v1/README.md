# NPU E2E Evaluation Campaign: `llm_attention_tail_v1`

This is the first repeated attention-tail campaign after `llm_smoke_v1`.

What it does:
- uses model-set identity `llm_attention_tail_v1`,
- exercises 2-4 repeated non-terminal `Softmax` episodes per model path,
- sweeps sequence length across `32`, `64`, and `128`,
- keeps architecture scope narrow to existing `fp16_nm1` and `fp16_nm2` points.

Manifest:
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign.json \
  --check_paths
```

Expected analysis fields:
- per-model token-equivalent latency
- steady-state throughput
- softmax issue and completion counts
- softmax busy time and occupancy
- queue stall buckets for softmax, DMA, GEMM, misc compute, and dependency wait
- tensor-equivalence summaries from the RTL/perf trace comparison path where RTL
  simulation is available

Boundary:
- This campaign is still an attention-proxy performance and equivalence stage.
- Decoder-quality claims still require the later dataset-backed decoder stage.
