# attention_decode_score_tile_int8_1x8 Equivalence

- decision: `attention_decode_score_tile_int8_1x8_equivalence_pass`
- equivalence pass: `True`
- semantic profile: `llama_decode_qk_score_row_m1_n8_s8_s8_acc32`
- reference: `python_signed_m1_n8_dot_products`
- focused tests passed: `1`
- test target: `tests/test_dense_gemm_tile_stream.py::test_packed_decode_score_tile_matches_reference_and_protocol`
