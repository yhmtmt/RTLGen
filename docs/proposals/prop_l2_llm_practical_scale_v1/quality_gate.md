# Quality Gate

- `proposal_id`: `prop_l2_llm_practical_scale_v1`
- campaign: `runs/campaigns/npu/e2e_eval_llm_practical_scale_v1/campaign.json`
- model set: `runs/models/llm_practical_scale_v1/manifest.json`

Required local checks:

```sh
python3 -m py_compile npu/mapper/examples/gen_llm_practical_scale_suite_lite.py
python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_scale_v1/campaign.json --check_paths
python3 npu/eval/gen_llm_reference_suite.py --manifest runs/models/llm_practical_scale_v1/manifest.json
python3 npu/eval/gen_llm_candidate_suite.py --manifest runs/models/llm_practical_scale_v1/manifest.json
python3 npu/eval/compare_llm_reference.py --reference-json runs/models/llm_practical_scale_v1/reference/practical_scale_attn6_s64_h64_kv2048.json --candidate-json runs/models/llm_practical_scale_v1/candidate/practical_scale_attn6_s64_h64_kv2048.json
```

Evaluator check:

```sh
python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_scale_v1/campaign.json --jobs 2 --batch_id l2_llm_practical_scale_v1_r1
python3 npu/eval/report_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_practical_scale_v1/campaign.json
```
