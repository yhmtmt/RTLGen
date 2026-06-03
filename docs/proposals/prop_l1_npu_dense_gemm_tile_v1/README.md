# Dense FP16 GEMM Tile V1

This proposal introduces a dense FP16 GEMM-tile architecture point to test
whether RTLGen can improve compute density beyond the corrected dynamic
dispatcher baseline.

The first evaluation measures `4x4` and `8x8` exact-FP16 MAC arrays with narrow
self-stimulating wrapper IO and no replicated vector tail. The result is a
planning gate for whether the Llama7B frontier should pursue dense compute
tiles, precision changes, or return to memory/NoC modeling.
