# Quality Gate

## Proposal

- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_sram_noc_softmax_recip_lut_frontier_v1`
- `title`: `Llama7B endpoint SRAM/NoC frontier with reciprocal-LUT softmax profiles`

## Checks

- q8 standalone PPA
  - `runs/designs/activations/attention_softmax_weight_int8_r8_acc24_recip_q8_wrapper/metrics.csv`
  - at least one `ok` row
- generated local-cost file
  - includes exactly the q8/q10/q12 profiles selected by the L2 item
  - cites the metrics path used for each softmax profile
- L2 full search
  - consumes `--topology-pairs-json`, not `--topology-derived-json`
  - does not reintroduce independent `--noc-bandwidth-bytes-per-cycle` or `--noc-hops`
  - reports `measured_l1_profile` in the best row
- precision accounting
  - selected profile must be interpreted together with the reciprocal-LUT quality
    gate, not as final Llama7B perplexity evidence

## Local Smoke Commands

- `python3 npu/eval/build_llama7b_attention_recip_lut_local_costs.py --repo-root . --base-costs runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_endpoint_v1.json --template-profile hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 --bits-list 10,12 --out /tmp/recip_lut_costs_q10_q12.json`
- `PYTHONPATH=control_plane pytest control_plane/control_plane/tests/test_l2_task_generator.py -k endpoint_sram_noc_full_search`
