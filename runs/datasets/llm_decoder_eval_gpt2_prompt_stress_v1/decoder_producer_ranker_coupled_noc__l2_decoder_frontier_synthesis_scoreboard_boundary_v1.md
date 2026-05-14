# Decoder Producer/Ranker Coupling

- model: `decoder_output_projection_producer_ranker_coupling_v1`
- mode: `coupled_noc`
- producer_service_best: `shared_gemm_stage_serial w128 ii768`
- coupled_best: `shared_gemm_stage_serial w64 k1 ii384`
- producer_control_boundary: `softmax_event_guard_synth_ok_under_bound cq_v1_softmax_event_guard ok`
- producer_control_boundary_elapsed_s: `196.19542427099077`

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

## Coupled Ranker Sweep

| scenario | vocab | hidden | W | top_k | MAC/cycle | share | producer_ii | producer_us | ranker_us | coupled_us | fifo ok | candidate_bytes | traffic reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| shared_gemm_stage_serial | 50257 | 768 | 64 | 1 | 8192 | 1.0 | 1536 | 1205.79 | 20184.701012 | 20184.701012 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 4 | 8192 | 1.0 | 1536 | 1205.79 | 22377.510697 | 22377.510697 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 1 | 8192 | 1.0 | 384 | 301.452 | 5046.275694 | 5046.275694 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 4 | 8192 | 1.0 | 384 | 301.452 | 5594.489027 | 5594.489027 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 1 | 32768 | 1.0 | 1536 | 1205.786 | 20184.701012 | 20184.701012 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 4 | 32768 | 1.0 | 1536 | 1205.786 | 22377.510697 | 22377.510697 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 1 | 32768 | 1.0 | 384 | 301.448 | 5046.275694 | 5046.275694 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 768 | 64 | 4 | 32768 | 1.0 | 384 | 301.448 | 5594.489027 | 5594.489027 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 1 | 8192 | 1.0 | 3072 | 1204.26 | 23518.819552 | 23518.819552 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 4 | 8192 | 1.0 | 3072 | 1204.26 | 26073.838587 | 26073.838587 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 1 | 8192 | 1.0 | 768 | 301.074 | 5879.822069 | 5879.822069 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 4 | 8192 | 1.0 | 768 | 301.074 | 6518.589558 | 6518.589558 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 1 | 32768 | 1.0 | 3072 | 1204.251 | 23518.819552 | 23518.819552 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 4 | 32768 | 1.0 | 3072 | 1204.251 | 26073.838587 | 26073.838587 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 1 | 32768 | 1.0 | 768 | 301.065 | 5879.822069 | 5879.822069 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 768 | 128 | 4 | 32768 | 1.0 | 768 | 301.065 | 6518.589558 | 6518.589558 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 1 | 8192 | 1.0 | 6144 | 1204.272 | 26878.650917 | 26878.650917 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 4 | 8192 | 1.0 | 6144 | 1204.272 | 29798.672671 | 29798.672671 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 1 | 8192 | 1.0 | 1536 | 301.086 | 6719.79665 | 6719.79665 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 4 | 8192 | 1.0 | 1536 | 301.086 | 7449.816637 | 7449.816637 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 1 | 32768 | 1.0 | 6144 | 1204.254 | 26878.650917 | 26878.650917 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 4 | 32768 | 1.0 | 6144 | 1204.254 | 29798.672671 | 29798.672671 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 1 | 32768 | 1.0 | 1536 | 301.068 | 6719.79665 | 6719.79665 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 768 | 256 | 4 | 32768 | 1.0 | 1536 | 301.068 | 7449.816637 | 7449.816637 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 1 | 8192 | 1.0 | 2048 | 1607.72 | 26912.890043 | 26912.890043 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 4 | 8192 | 1.0 | 2048 | 1607.72 | 29836.631439 | 29836.631439 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 1 | 8192 | 1.0 | 512 | 401.936 | 6728.322951 | 6728.322951 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 4 | 8192 | 1.0 | 512 | 401.936 | 7459.269212 | 7459.269212 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 1 | 32768 | 1.0 | 2048 | 1607.714 | 26912.890043 | 26912.890043 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 4 | 32768 | 1.0 | 2048 | 1607.714 | 29836.631439 | 29836.631439 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 1 | 32768 | 1.0 | 512 | 401.93 | 6728.322951 | 6728.322951 | `True` | 6292 | 0.968701 |
| shared_gemm_stage_serial | 50257 | 1024 | 64 | 4 | 32768 | 1.0 | 512 | 401.93 | 7459.269212 | 7459.269212 | `True` | 25168 | 0.874804 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 1 | 8192 | 1.0 | 4096 | 1605.68 | 31358.37399 | 31358.37399 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 4 | 8192 | 1.0 | 4096 | 1605.68 | 34765.060378 | 34765.060378 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 1 | 8192 | 1.0 | 1024 | 401.432 | 7839.710678 | 7839.710678 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 4 | 8192 | 1.0 | 1024 | 401.432 | 8691.395005 | 8691.395005 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 1 | 32768 | 1.0 | 4096 | 1605.668 | 31358.37399 | 31358.37399 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 4 | 32768 | 1.0 | 4096 | 1605.668 | 34765.060378 | 34765.060378 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 1 | 32768 | 1.0 | 1024 | 401.42 | 7839.710678 | 7839.710678 | `True` | 3148 | 0.98434 |
| shared_gemm_stage_serial | 50257 | 1024 | 128 | 4 | 32768 | 1.0 | 1024 | 401.42 | 8691.395005 | 8691.395005 | `True` | 12592 | 0.937362 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 1 | 8192 | 1.0 | 8192 | 1605.696 | 35838.141702 | 35838.141702 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 4 | 8192 | 1.0 | 8192 | 1605.696 | 39731.497574 | 39731.497574 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 1 | 8192 | 1.0 | 2048 | 401.448 | 8959.669347 | 8959.669347 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 4 | 8192 | 1.0 | 2048 | 401.448 | 9933.022863 | 9933.022863 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 1 | 32768 | 1.0 | 8192 | 1605.672 | 35838.141702 | 35838.141702 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 4 | 32768 | 1.0 | 8192 | 1605.672 | 39731.497574 | 39731.497574 | `True` | 6320 | 0.968562 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 1 | 32768 | 1.0 | 2048 | 401.424 | 8959.669347 | 8959.669347 | `True` | 1580 | 0.99214 |
| shared_gemm_stage_serial | 50257 | 1024 | 256 | 4 | 32768 | 1.0 | 2048 | 401.424 | 9933.022863 | 9933.022863 | `True` | 6320 | 0.968562 |

## Assumptions

- Producer means only the final decoder output-projection logit source.
- Shared GEMM is stage-serialized: attention/MLP have completed before output projection starts.
- producer_ii_cycles is derived as max(compute cycles per tile, weight-memory service cycles per tile).
- Hidden vector load is charged once per token; output projection weights are streamed per vocabulary tile.
- shared_noc_contention reduces effective producer memory bandwidth by memory_share.
- Ranker coupling reuses the ready-valid logit-rank model and preserves its equivalence observables.
- If producer_control_boundary is present, it is control-path synthesis feasibility evidence; it does not replace the output-projection service model.
