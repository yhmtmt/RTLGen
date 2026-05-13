# Output-Projection Producer Scale

The merged decoder frontier synthesis says the current dominant component is
`output_projection_producer_ranker`. The best synthesis rows use producer width
64 and integer producer II values of 384 to 512 cycles, but the measured
producer-side PPA anchors are currently much smaller.

This proposal measures fp16 GEMM producer blocks at `num_modules=4`, `8`, and
`16` with the `gemm_compute_array` hierarchy preserved. These points should be
used as producer-side scaling anchors before selecting the first combined
producer/ranker macro.

The result is not final decoder PPA. It does not yet include vocabulary weight
SRAM, shared NoC arbitration, or the global top-k merge path.
