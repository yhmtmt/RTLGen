# Decoder Producer/Ranker Coupling

- model: `decoder_output_projection_producer_ranker_coupling_v1`
- mode: `producer_service`
- producer_service_best: `shared_gemm_stage_serial w128 ii768`

## Producer Service Sweep

| scenario | vocab | hidden | W | MAC/cycle | BW | share | II | limiter | latency_us | weight_bytes/token |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| shared_gemm_stage_serial | 50257 | 768 | 64 | 8192 | 64.0 | 1.0 | 1536 | weight_memory | 1205.79 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 8192 | 256.0 | 1.0 | 384 | weight_memory | 301.452 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 32768 | 64.0 | 1.0 | 1536 | weight_memory | 1205.786 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 32768 | 256.0 | 1.0 | 384 | weight_memory | 301.448 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 8192 | 64.0 | 1.0 | 3072 | weight_memory | 1204.26 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 8192 | 256.0 | 1.0 | 768 | weight_memory | 301.074 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 32768 | 64.0 | 1.0 | 3072 | weight_memory | 1204.251 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 32768 | 256.0 | 1.0 | 768 | weight_memory | 301.065 | 77266944 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 8192 | 64.0 | 1.0 | 6144 | weight_memory | 1204.272 | 77463552 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 8192 | 256.0 | 1.0 | 1536 | weight_memory | 301.086 | 77463552 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 32768 | 64.0 | 1.0 | 6144 | weight_memory | 1204.254 | 77463552 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 32768 | 256.0 | 1.0 | 1536 | weight_memory | 301.068 | 77463552 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 8192 | 64.0 | 1.0 | 2048 | weight_memory | 1607.72 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 8192 | 256.0 | 1.0 | 512 | weight_memory | 401.936 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 32768 | 64.0 | 1.0 | 2048 | weight_memory | 1607.714 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 32768 | 256.0 | 1.0 | 512 | weight_memory | 401.93 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 8192 | 64.0 | 1.0 | 4096 | weight_memory | 1605.68 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 8192 | 256.0 | 1.0 | 1024 | weight_memory | 401.432 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 32768 | 64.0 | 1.0 | 4096 | weight_memory | 1605.668 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 32768 | 256.0 | 1.0 | 1024 | weight_memory | 401.42 | 103022592 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 8192 | 64.0 | 1.0 | 8192 | weight_memory | 1605.696 | 103284736 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 8192 | 256.0 | 1.0 | 2048 | weight_memory | 401.448 | 103284736 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 32768 | 64.0 | 1.0 | 8192 | weight_memory | 1605.672 | 103284736 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 32768 | 256.0 | 1.0 | 2048 | weight_memory | 401.424 | 103284736 |
| shared_gemm_stage_serial | 50257 | 2048 | 64 | 8192 | 64.0 | 1.0 | 4096 | weight_memory | 3215.44 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 64 | 8192 | 256.0 | 1.0 | 1024 | weight_memory | 803.872 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 64 | 32768 | 64.0 | 1.0 | 4096 | weight_memory | 3215.428 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 64 | 32768 | 256.0 | 1.0 | 1024 | weight_memory | 803.86 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 128 | 8192 | 64.0 | 1.0 | 8192 | weight_memory | 3211.36 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 128 | 8192 | 256.0 | 1.0 | 2048 | weight_memory | 802.864 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 128 | 32768 | 64.0 | 1.0 | 8192 | weight_memory | 3211.336 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 128 | 32768 | 256.0 | 1.0 | 2048 | weight_memory | 802.84 | 206045184 |
| shared_gemm_stage_serial | 50257 | 2048 | 256 | 8192 | 64.0 | 1.0 | 16384 | weight_memory | 3211.392 | 206569472 |
| shared_gemm_stage_serial | 50257 | 2048 | 256 | 8192 | 256.0 | 1.0 | 4096 | weight_memory | 802.896 | 206569472 |
| shared_gemm_stage_serial | 50257 | 2048 | 256 | 32768 | 64.0 | 1.0 | 16384 | weight_memory | 3211.344 | 206569472 |
| shared_gemm_stage_serial | 50257 | 2048 | 256 | 32768 | 256.0 | 1.0 | 4096 | weight_memory | 802.848 | 206569472 |
| shared_gemm_stage_serial | 100000 | 768 | 64 | 8192 | 64.0 | 1.0 | 1536 | weight_memory | 2399.262 | 153649152 |
| shared_gemm_stage_serial | 100000 | 768 | 64 | 8192 | 256.0 | 1.0 | 384 | weight_memory | 599.82 | 153649152 |
| shared_gemm_stage_serial | 100000 | 768 | 64 | 32768 | 64.0 | 1.0 | 1536 | weight_memory | 2399.258 | 153649152 |
| shared_gemm_stage_serial | 100000 | 768 | 64 | 32768 | 256.0 | 1.0 | 384 | weight_memory | 599.816 | 153649152 |
| shared_gemm_stage_serial | 100000 | 768 | 128 | 8192 | 64.0 | 1.0 | 3072 | weight_memory | 2399.268 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 128 | 8192 | 256.0 | 1.0 | 768 | weight_memory | 599.826 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 128 | 32768 | 64.0 | 1.0 | 3072 | weight_memory | 2399.259 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 128 | 32768 | 256.0 | 1.0 | 768 | weight_memory | 599.817 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 256 | 8192 | 64.0 | 1.0 | 6144 | weight_memory | 2396.208 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 256 | 8192 | 256.0 | 1.0 | 1536 | weight_memory | 599.07 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 256 | 32768 | 64.0 | 1.0 | 6144 | weight_memory | 2396.19 | 153747456 |
| shared_gemm_stage_serial | 100000 | 768 | 256 | 32768 | 256.0 | 1.0 | 1536 | weight_memory | 599.052 | 153747456 |

## Assumptions

- Producer means only the final decoder output-projection logit source.
- Shared GEMM is stage-serialized: attention/MLP have completed before output projection starts.
- producer_ii_cycles is derived as max(compute cycles per tile, weight-memory service cycles per tile).
- Hidden vector load is charged once per token; output projection weights are streamed per vocabulary tile.
- shared_noc_contention reduces effective producer memory bandwidth by memory_share.
- Ranker coupling reuses the ready-valid logit-rank model and preserves its equivalence observables.
