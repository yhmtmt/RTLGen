# NPU E2E Evaluation Campaign: `llm_attention_tail_stress_v1`

This is the bounded stress campaign after `llm_attention_tail_v1`.

What it does:
- uses model-set identity `llm_attention_tail_stress_v1`,
- exercises 4-6 repeated non-terminal `Softmax` episodes per model path,
- adds sequence length `256` while retaining one `128` reference stress point,
- keeps architecture scope narrow to existing `fp16_nm1` and `fp16_nm2` points.

Manifest:
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json \
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
- If pressure remains low, the next step should be a richer decoder-style
  benchmark before proposing softmax-specific datapath changes.
