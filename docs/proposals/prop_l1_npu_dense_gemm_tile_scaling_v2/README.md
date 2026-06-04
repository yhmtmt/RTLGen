# Dense FP16 GEMM Tile Scaling V2

This proposal measures whether the dense FP16 GEMM tile density observed at
8x8 holds at larger 128- and 256-MAC/cycle tile sizes.

The result is the physical anchor for deciding whether the Llama7B
attention/KV frontier can use dense compute macros, or whether the 8x8 density
was only a small-tile artifact.
