# Dense FP16 GEMM Tile Scaling V3

This proposal measures whether the current best exact-FP16 dense GEMM tile can
gain useful MAC density by increasing `k_unroll` inside the existing 16x16
generator limit.

PR #981 showed that the abstract `524288 MAC/cycle` Llama7B frontier is not
physically plausible when replaced by measured dense-tile compute capacity. The
next question is whether a denser measured tile can improve the corrected
frontier before changing precision or inventing a wider generator.

The immediate evaluator job reruns the 16x16 baseline in the same larger macro
floorplan as the new depth point, then measures `16x16 k2 p2`. A `16x16 k4 p2`
config is prepared as a later boundary item after the k2 result is reviewed.
