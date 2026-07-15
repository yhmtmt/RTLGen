# attention_decode_score_tile_int8_1x8

Exact signed-int8 Llama7B decode score tile for one query and eight key rows.
Each accepted beat consumes one signed query scalar and eight signed key
scalars. The tile accumulates eight signed 32-bit dot products and emits them
as one ready/valid 256-bit score row.

Lane `j` occupies `result_score_row[j*32 +: 32]`, matching
`attention_two_pass_stream_iterdiv.fill_score_row`. This removes the scalar
result packer required by the generic operational GEMM tile.
