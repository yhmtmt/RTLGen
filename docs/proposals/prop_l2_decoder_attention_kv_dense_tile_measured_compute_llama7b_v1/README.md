# Llama7B Dense Tile Measured Compute Substitution

This proposal queues an L2 frontier-detail job that substitutes merged dense
FP16 GEMM tile PPA into the Llama7B 131k physical-HBM memory/NoC model.

The focused question is whether the dense tile scaling result from PR #764
selects a better measured compute anchor than the older nm-count compute blocks,
and which die/logic budget reaches the practical HBM floor.

The job consumes existing merged evidence only:

- `l1_npu_dense_gemm_tile_scaling_v2`
- `l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2`

It also reads the materialized physical-HBM memory/NoC JSON already present in
`runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/`; that artifact is not
listed as a DB dependency because clean control-plane DBs may not retain the
older work item row.
