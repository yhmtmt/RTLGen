# dense_gemm_tile_stream_int8_16x8

Operational signed-int8 outer-product tile with 128 independently observable
signed 32-bit accumulators. Inputs arrive as 16 A lanes and 8 B lanes. Results
drain as a scalar ready/valid row-major stream.

Unlike `npu_dense_gemm_tile_int8_16x8_k1_p1`, this design includes complete
accumulator state and does not use a result hash as its functional interface.
