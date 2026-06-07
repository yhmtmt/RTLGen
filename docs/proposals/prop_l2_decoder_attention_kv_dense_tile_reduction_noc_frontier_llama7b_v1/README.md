# Llama7B Dense Tile Reduction/NoC Frontier

This proposal queues a focused L2 frontier-detail job around the selected
`dense_gemm_16x8_k1_p1` compute anchor from the dense tile all-measured
clustered schedule result.

The previous result showed that the frontier is no longer only raw GEMM
throughput: the best point reaches `132480` MAC/cycle, while cross-tile
reduction and analytic SRAM/global NoC service are the main residual
abstractions. This job keeps the measured dense compute and measured local L1
profile fixed, then sweeps cluster count, local/shared SRAM placement, global
NoC bandwidth/hops, command overhead, and reduction overhead.

The expected output is a ranked frontier that separates compute-bound,
reduction-bound, shared-SRAM/NoC-bound, and HBM-sensitive candidate regions.
