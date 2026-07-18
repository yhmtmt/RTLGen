# Llama7B GQA8 Folded Query-Head Lane Equivalence

- decision: `llama7b_gqa8_folded_lane_equivalence_pass`
- equivalence pass: `True`
- shared result hash: `e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069`
- precision contract: `exact_signed_int8_qkv_s32_score_lut_softmax_integer_output`

| lanes | waves | macros | cycles | Q/K replays | value reads/block | pass |
|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 8 | 56 | 66671 | 8 | 128 | True |
| 2 | 4 | 112 | 62199 | 4 | 64 | True |
| 4 | 2 | 224 | 59963 | 2 | 32 | True |
| 8 | 1 | 448 | 58845 | 1 | 16 | True |

Each of 8/L waves replays one complete packed Q/K packet; no hidden query or key buffer is assumed.
