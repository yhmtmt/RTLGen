# Llama7B composed decode-score cluster correction

- decision: `prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only`
- retracted prior best: `669.792507491203` token/s
- composed no-stall throughput upper bound: `0.521229054458` token/s
- corresponding area: `634.909914937` mm2
- energy promotion: `blocked`

| candidate | clusters | waves/layer | QKV tiles | latency us | token/s | area mm2 | fit |
|---|---:|---:|---:|---:|---:|---:|---|
| decode_score_local_cluster_c32_vl1 | 32 | 16 | 640 | 7671625.89864 | 0.130350464584 | 375.448794937 | True |
| decode_score_local_cluster_c64_vl1 | 64 | 8 | 640 | 3836236.846992 | 0.260672122156 | 461.935834937 | True |
| decode_score_local_cluster_c96_vl1 | 96 | 6 | 640 | 2877389.58408 | 0.347537228025 | 548.422874937 | True |
| decode_score_local_cluster_c128_vl1 | 128 | 4 | 640 | 1918542.321168 | 0.521229054458 | 634.909914937 | True |
| decode_score_local_cluster_c144_vl1 | 144 | 4 | 640 | 1918542.321168 | 0.521229054458 | 678.153434937 | True |
| decode_score_local_cluster_c147_vl1 | 147 | 4 | 303 | 1919483.034058 | 0.520973607089 | 683.268178957 | True |
| decode_score_local_cluster_c32_vl4 | 32 | 16 | 640 | 7833651.023299 | 0.127654397295 | 375.448794937 | True |
| decode_score_local_cluster_c64_vl4 | 64 | 8 | 640 | 3917249.409322 | 0.255281166836 | 461.935834937 | True |
| decode_score_local_cluster_c96_vl4 | 96 | 6 | 640 | 2938149.005827 | 0.34035033554 | 548.422874937 | True |
| decode_score_local_cluster_c128_vl4 | 128 | 4 | 640 | 1959048.602333 | 0.510451858524 | 634.909914937 | True |
| decode_score_local_cluster_c144_vl4 | 144 | 4 | 640 | 1959048.602333 | 0.510451858524 | 678.153434937 | True |
| decode_score_local_cluster_c147_vl4 | 147 | 4 | 303 | 1959989.315222 | 0.510206862983 | 683.268178957 | True |
| decode_score_local_cluster_c32_vl8 | 32 | 16 | 640 | 8049684.522845 | 0.124228470962 | 375.448794937 | True |
| decode_score_local_cluster_c64_vl8 | 64 | 8 | 640 | 4025266.159094 | 0.248430777115 | 461.935834937 | True |
| decode_score_local_cluster_c96_vl8 | 96 | 6 | 640 | 3019161.568157 | 0.331217782628 | 548.422874937 | True |
| decode_score_local_cluster_c128_vl8 | 128 | 4 | 640 | 2013056.977219 | 0.496756928053 | 634.909914937 | True |
| decode_score_local_cluster_c144_vl8 | 144 | 4 | 640 | 2013056.977219 | 0.496756928053 | 678.153434937 | True |
| decode_score_local_cluster_c147_vl8 | 147 | 4 | 303 | 2013997.690109 | 0.496524899165 | 683.268178957 | True |
