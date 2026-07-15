# dense_gemm_tile_stream_int8_1x8

Exact signed-int8 `M=1, N=8` outer-product stream for single-token decoder
QK scoring. One query scalar and eight key scalars are accepted per head-dimension
beat. Eight signed 32-bit scores drain as a scalar ready/valid stream.

This is the scalar-drain control point for the packed decode-score tile. Both
variants compute the same eight scores; only the result interface differs.
