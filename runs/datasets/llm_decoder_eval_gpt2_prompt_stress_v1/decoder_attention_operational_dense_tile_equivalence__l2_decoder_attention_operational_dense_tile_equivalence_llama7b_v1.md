# operational_dense_gemm_tile_int8_16x8 Equivalence

- decision: `operational_dense_gemm_tile_int8_16x8_equivalence_pass`
- equivalence pass: `True`
- semantic profile: `operational_dense_gemm_outer_product_stream_s8_s8_acc32`
- reference: `python_signed_outer_product_gemm`
- focused tests passed: `2`
- test target: `tests/test_dense_gemm_tile_stream.py`
