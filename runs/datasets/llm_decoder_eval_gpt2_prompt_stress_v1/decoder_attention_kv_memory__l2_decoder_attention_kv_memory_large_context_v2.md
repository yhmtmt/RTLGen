# Decoder Attention/KV Memory Breakdown

- model: `llm_decoder_attention_kv_memory_v1`

## Focus Summary

| shape | seq | tier | share | bits | hops | total_us | dominant | dom_share | kv_byte_share | kv_cycle_share | eff_kv_B/cyc | intensity |
|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| gpt2_medium_proxy | 2048 | hbm | gqa4 | 4 | 1 | 424.56 | qk_score | 0.520972 | 0.791651 | 0.984511 | 64.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | hbm | gqa4 | 4 | 2 | 424.56 | qk_score | 0.520972 | 0.791651 | 0.984511 | 64.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | hbm | gqa4 | 4 | 4 | 424.56 | qk_score | 0.520972 | 0.791651 | 0.984511 | 64.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | hbm | mqa | 4 | 1 | 129.48 | qk_score | 0.569416 | 0.4882 | 0.949398 | 64.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | hbm | mqa | 4 | 2 | 129.48 | qk_score | 0.569416 | 0.4882 | 0.949398 | 64.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | hbm | mqa | 4 | 4 | 129.48 | qk_score | 0.569416 | 0.4882 | 0.949398 | 64.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | remote_hbm | gqa4 | 4 | 1 | 842.544 | qk_score | 0.525038 | 0.791651 | 0.992195 | 32.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | remote_hbm | gqa4 | 4 | 2 | 842.544 | qk_score | 0.525038 | 0.791651 | 0.992195 | 32.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | remote_hbm | gqa4 | 4 | 4 | 842.544 | qk_score | 0.525038 | 0.791651 | 0.992195 | 32.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | remote_hbm | mqa | 4 | 1 | 252.408 | qk_score | 0.584197 | 0.4882 | 0.974042 | 32.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | remote_hbm | mqa | 4 | 2 | 252.408 | qk_score | 0.584197 | 0.4882 | 0.974042 | 32.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | remote_hbm | mqa | 4 | 4 | 252.408 | qk_score | 0.584197 | 0.4882 | 0.974042 | 32.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | shared_sram | gqa4 | 4 | 1 | 111.072 | qk_score | 0.497839 | 0.791651 | 0.940795 | 256.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | shared_sram | gqa4 | 4 | 2 | 215.568 | qk_score | 0.513026 | 0.791651 | 0.969495 | 128.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | shared_sram | gqa4 | 4 | 4 | 424.56 | qk_score | 0.520972 | 0.791651 | 0.984511 | 64.0 | 5.145729 |
| gpt2_medium_proxy | 2048 | shared_sram | mqa | 4 | 1 | 37.296 | qk_score | 0.494208 | 0.4882 | 0.824324 | 256.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | shared_sram | mqa | 4 | 2 | 68.016 | qk_score | 0.54199 | 0.4882 | 0.90367 | 128.0 | 11.960906 |
| gpt2_medium_proxy | 2048 | shared_sram | mqa | 4 | 4 | 129.48 | qk_score | 0.569416 | 0.4882 | 0.949398 | 64.0 | 11.960906 |
| gpt2_medium_proxy | 131072 | hbm | gqa4 | 4 | 1 | 27132.528 | qk_score | 0.521727 | 0.799868 | 0.985492 | 64.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | hbm | gqa4 | 4 | 2 | 27132.528 | qk_score | 0.521727 | 0.799868 | 0.985492 | 64.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | hbm | gqa4 | 4 | 4 | 27132.528 | qk_score | 0.521727 | 0.799868 | 0.985492 | 64.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | hbm | mqa | 4 | 1 | 8257.992 | qk_score | 0.571397 | 0.499811 | 0.952334 | 64.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | hbm | mqa | 4 | 2 | 8257.992 | qk_score | 0.571397 | 0.499811 | 0.952334 | 64.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | hbm | mqa | 4 | 4 | 8257.992 | qk_score | 0.571397 | 0.499811 | 0.952334 | 64.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | remote_hbm | gqa4 | 4 | 1 | 53871.408 | qk_score | 0.525539 | 0.799868 | 0.992693 | 32.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | remote_hbm | gqa4 | 4 | 2 | 53871.408 | qk_score | 0.525539 | 0.799868 | 0.992693 | 32.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | remote_hbm | gqa4 | 4 | 4 | 53871.408 | qk_score | 0.525539 | 0.799868 | 0.992693 | 32.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | remote_hbm | mqa | 4 | 1 | 16122.36 | qk_score | 0.585348 | 0.499811 | 0.975585 | 32.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | remote_hbm | mqa | 4 | 2 | 16122.36 | qk_score | 0.585348 | 0.499811 | 0.975585 | 32.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | remote_hbm | mqa | 4 | 4 | 16122.36 | qk_score | 0.585348 | 0.499811 | 0.975585 | 32.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | shared_sram | gqa4 | 4 | 1 | 7078.368 | qk_score | 0.499966 | 0.799868 | 0.944387 | 256.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | shared_sram | gqa4 | 4 | 2 | 13763.088 | qk_score | 0.514266 | 0.799868 | 0.971398 | 128.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | shared_sram | gqa4 | 4 | 4 | 27132.528 | qk_score | 0.521727 | 0.799868 | 0.985492 | 64.0 | 3.230718 |
| gpt2_medium_proxy | 131072 | shared_sram | mqa | 4 | 1 | 2359.728 | qk_score | 0.499908 | 0.499811 | 0.833191 | 256.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | shared_sram | mqa | 4 | 2 | 4325.808 | qk_score | 0.5454 | 0.499811 | 0.909006 | 128.0 | 8.063361 |
| gpt2_medium_proxy | 131072 | shared_sram | mqa | 4 | 4 | 8257.992 | qk_score | 0.571397 | 0.499811 | 0.952334 | 64.0 | 8.063361 |
| gpt2_small | 2048 | hbm | gqa4 | 4 | 1 | 159.216 | qk_score | 0.520953 | 0.791651 | 0.984474 | 64.0 | 4.650947 |
| gpt2_small | 2048 | hbm | gqa4 | 4 | 2 | 159.216 | qk_score | 0.520953 | 0.791651 | 0.984474 | 64.0 | 4.650947 |
| gpt2_small | 2048 | hbm | gqa4 | 4 | 4 | 159.216 | qk_score | 0.520953 | 0.791651 | 0.984474 | 64.0 | 4.650947 |
| gpt2_small | 2048 | hbm | mqa | 4 | 1 | 60.852 | qk_score | 0.555315 | 0.559716 | 0.959574 | 64.0 | 9.445204 |
| gpt2_small | 2048 | hbm | mqa | 4 | 2 | 60.852 | qk_score | 0.555315 | 0.559716 | 0.959574 | 64.0 | 9.445204 |
| gpt2_small | 2048 | hbm | mqa | 4 | 4 | 60.852 | qk_score | 0.555315 | 0.559716 | 0.959574 | 64.0 | 9.445204 |
| gpt2_small | 2048 | remote_hbm | gqa4 | 4 | 1 | 315.96 | qk_score | 0.525028 | 0.791651 | 0.992176 | 32.0 | 4.650947 |
| gpt2_small | 2048 | remote_hbm | gqa4 | 4 | 2 | 315.96 | qk_score | 0.525028 | 0.791651 | 0.992176 | 32.0 | 4.650947 |
| gpt2_small | 2048 | remote_hbm | gqa4 | 4 | 4 | 315.96 | qk_score | 0.525028 | 0.791651 | 0.992176 | 32.0 | 4.650947 |
| gpt2_small | 2048 | remote_hbm | mqa | 4 | 1 | 119.244 | qk_score | 0.566771 | 0.559716 | 0.97937 | 32.0 | 9.445204 |
| gpt2_small | 2048 | remote_hbm | mqa | 4 | 2 | 119.244 | qk_score | 0.566771 | 0.559716 | 0.97937 | 32.0 | 9.445204 |
| gpt2_small | 2048 | remote_hbm | mqa | 4 | 4 | 119.244 | qk_score | 0.566771 | 0.559716 | 0.97937 | 32.0 | 9.445204 |
| gpt2_small | 2048 | shared_sram | gqa4 | 4 | 1 | 41.664 | qk_score | 0.497696 | 0.791651 | 0.940668 | 256.0 | 4.650947 |
| gpt2_small | 2048 | shared_sram | gqa4 | 4 | 2 | 80.844 | qk_score | 0.512988 | 0.791651 | 0.969423 | 128.0 | 4.650947 |
| gpt2_small | 2048 | shared_sram | gqa4 | 4 | 4 | 159.216 | qk_score | 0.520953 | 0.791651 | 0.984474 | 64.0 | 4.650947 |
| gpt2_small | 2048 | shared_sram | mqa | 4 | 1 | 17.064 | qk_score | 0.495077 | 0.559716 | 0.855837 | 256.0 | 9.445204 |
| gpt2_small | 2048 | shared_sram | mqa | 4 | 2 | 31.656 | qk_score | 0.533738 | 0.559716 | 0.92229 | 128.0 | 9.445204 |
| gpt2_small | 2048 | shared_sram | mqa | 4 | 4 | 60.852 | qk_score | 0.555315 | 0.559716 | 0.959574 | 64.0 | 9.445204 |
| gpt2_small | 131072 | hbm | gqa4 | 4 | 1 | 10174.704 | qk_score | 0.521727 | 0.799868 | 0.985491 | 64.0 | 3.222906 |
| gpt2_small | 131072 | hbm | gqa4 | 4 | 2 | 10174.704 | qk_score | 0.521727 | 0.799868 | 0.985491 | 64.0 | 3.222906 |
| gpt2_small | 131072 | hbm | gqa4 | 4 | 4 | 10174.704 | qk_score | 0.521727 | 0.799868 | 0.985491 | 64.0 | 3.222906 |
| gpt2_small | 131072 | hbm | mqa | 4 | 1 | 3883.188 | qk_score | 0.556936 | 0.571242 | 0.961987 | 64.0 | 6.898414 |
| gpt2_small | 131072 | hbm | mqa | 4 | 2 | 3883.188 | qk_score | 0.556936 | 0.571242 | 0.961987 | 64.0 | 6.898414 |
| gpt2_small | 131072 | hbm | mqa | 4 | 4 | 3883.188 | qk_score | 0.556936 | 0.571242 | 0.961987 | 64.0 | 6.898414 |
| gpt2_small | 131072 | remote_hbm | gqa4 | 4 | 1 | 20201.784 | qk_score | 0.525539 | 0.799868 | 0.992693 | 32.0 | 3.222906 |
| gpt2_small | 131072 | remote_hbm | gqa4 | 4 | 2 | 20201.784 | qk_score | 0.525539 | 0.799868 | 0.992693 | 32.0 | 3.222906 |
| gpt2_small | 131072 | remote_hbm | gqa4 | 4 | 4 | 20201.784 | qk_score | 0.525539 | 0.799868 | 0.992693 | 32.0 | 3.222906 |
| gpt2_small | 131072 | remote_hbm | mqa | 4 | 1 | 7618.764 | qk_score | 0.567727 | 0.571242 | 0.980625 | 32.0 | 6.898414 |
| gpt2_small | 131072 | remote_hbm | mqa | 4 | 2 | 7618.764 | qk_score | 0.567727 | 0.571242 | 0.980625 | 32.0 | 6.898414 |
| gpt2_small | 131072 | remote_hbm | mqa | 4 | 4 | 7618.764 | qk_score | 0.567727 | 0.571242 | 0.980625 | 32.0 | 6.898414 |
| gpt2_small | 131072 | shared_sram | gqa4 | 4 | 1 | 2654.4 | qk_score | 0.499964 | 0.799868 | 0.944385 | 256.0 | 3.222906 |
| gpt2_small | 131072 | shared_sram | gqa4 | 4 | 2 | 5161.164 | qk_score | 0.514265 | 0.799868 | 0.971397 | 128.0 | 3.222906 |
| gpt2_small | 131072 | shared_sram | gqa4 | 4 | 4 | 10174.704 | qk_score | 0.521727 | 0.799868 | 0.985491 | 64.0 | 3.222906 |
| gpt2_small | 131072 | shared_sram | mqa | 4 | 1 | 1081.512 | qk_score | 0.499922 | 0.571242 | 0.863513 | 256.0 | 6.898414 |
| gpt2_small | 131072 | shared_sram | mqa | 4 | 2 | 2015.4 | qk_score | 0.536541 | 0.571242 | 0.926758 | 128.0 | 6.898414 |
| gpt2_small | 131072 | shared_sram | mqa | 4 | 4 | 3883.188 | qk_score | 0.556936 | 0.571242 | 0.961987 | 64.0 | 6.898414 |
| large_context_proxy | 2048 | hbm | gqa4 | 4 | 1 | 3411.4 | qk_score | 0.510289 | 0.878593 | 0.99103 | 64.0 | 14.496782 |
| large_context_proxy | 2048 | hbm | gqa4 | 4 | 2 | 3411.4 | qk_score | 0.510289 | 0.878593 | 0.99103 | 64.0 | 14.496782 |
| large_context_proxy | 2048 | hbm | gqa4 | 4 | 4 | 3411.4 | qk_score | 0.510289 | 0.878593 | 0.99103 | 64.0 | 14.496782 |
| large_context_proxy | 2048 | hbm | mqa | 4 | 1 | 459.96 | qk_score | 0.578833 | 0.422181 | 0.935386 | 64.0 | 60.160792 |
| large_context_proxy | 2048 | hbm | mqa | 4 | 2 | 459.96 | qk_score | 0.578833 | 0.422181 | 0.935386 | 64.0 | 60.160792 |
| large_context_proxy | 2048 | hbm | mqa | 4 | 4 | 459.96 | qk_score | 0.578833 | 0.422181 | 0.935386 | 64.0 | 60.160792 |
| large_context_proxy | 2048 | remote_hbm | gqa4 | 4 | 1 | 6792.2 | qk_score | 0.512588 | 0.878593 | 0.995495 | 32.0 | 14.496782 |
| large_context_proxy | 2048 | remote_hbm | gqa4 | 4 | 2 | 6792.2 | qk_score | 0.512588 | 0.878593 | 0.995495 | 32.0 | 14.496782 |
| large_context_proxy | 2048 | remote_hbm | gqa4 | 4 | 4 | 6792.2 | qk_score | 0.512588 | 0.878593 | 0.995495 | 32.0 | 14.496782 |
| large_context_proxy | 2048 | remote_hbm | mqa | 4 | 1 | 890.2 | qk_score | 0.598158 | 0.422181 | 0.966614 | 32.0 | 60.160792 |
| large_context_proxy | 2048 | remote_hbm | mqa | 4 | 2 | 890.2 | qk_score | 0.598158 | 0.422181 | 0.966614 | 32.0 | 60.160792 |
| large_context_proxy | 2048 | remote_hbm | mqa | 4 | 4 | 890.2 | qk_score | 0.598158 | 0.422181 | 0.966614 | 32.0 | 60.160792 |
| large_context_proxy | 2048 | shared_sram | gqa4 | 4 | 1 | 875.8 | qk_score | 0.496917 | 0.878593 | 0.965061 | 256.0 | 14.496782 |
| large_context_proxy | 2048 | shared_sram | gqa4 | 4 | 2 | 1721.0 | qk_score | 0.505752 | 0.878593 | 0.98222 | 128.0 | 14.496782 |
| large_context_proxy | 2048 | shared_sram | gqa4 | 4 | 4 | 3411.4 | qk_score | 0.510289 | 0.878593 | 0.99103 | 64.0 | 14.496782 |
| large_context_proxy | 2048 | shared_sram | mqa | 4 | 1 | 137.28 | qk_score | 0.484848 | 0.422181 | 0.783508 | 256.0 | 60.160792 |
| large_context_proxy | 2048 | shared_sram | mqa | 4 | 2 | 244.84 | qk_score | 0.543702 | 0.422181 | 0.878615 | 128.0 | 60.160792 |
| large_context_proxy | 2048 | shared_sram | mqa | 4 | 4 | 459.96 | qk_score | 0.578833 | 0.422181 | 0.935386 | 64.0 | 60.160792 |
| large_context_proxy | 131072 | hbm | gqa4 | 4 | 1 | 217913.8 | qk_score | 0.511263 | 0.888726 | 0.992458 | 64.0 | 3.728484 |
| large_context_proxy | 131072 | hbm | gqa4 | 4 | 2 | 217913.8 | qk_score | 0.511263 | 0.888726 | 0.992458 | 64.0 | 3.728484 |
| large_context_proxy | 131072 | hbm | gqa4 | 4 | 4 | 217913.8 | qk_score | 0.511263 | 0.888726 | 0.992458 | 64.0 | 3.728484 |
| large_context_proxy | 131072 | hbm | mqa | 4 | 1 | 29167.8 | qk_score | 0.584184 | 0.444079 | 0.943687 | 64.0 | 18.474361 |
| large_context_proxy | 131072 | hbm | mqa | 4 | 2 | 29167.8 | qk_score | 0.584184 | 0.444079 | 0.943687 | 64.0 | 18.474361 |
| large_context_proxy | 131072 | hbm | mqa | 4 | 4 | 29167.8 | qk_score | 0.584184 | 0.444079 | 0.943687 | 64.0 | 18.474361 |
| large_context_proxy | 131072 | remote_hbm | gqa4 | 4 | 1 | 434184.2 | qk_score | 0.513198 | 0.888726 | 0.996215 | 32.0 | 3.728484 |
| large_context_proxy | 131072 | remote_hbm | gqa4 | 4 | 2 | 434184.2 | qk_score | 0.513198 | 0.888726 | 0.996215 | 32.0 | 3.728484 |
| large_context_proxy | 131072 | remote_hbm | gqa4 | 4 | 4 | 434184.2 | qk_score | 0.513198 | 0.888726 | 0.996215 | 32.0 | 3.728484 |
| large_context_proxy | 131072 | remote_hbm | mqa | 4 | 1 | 56693.08 | qk_score | 0.601109 | 0.444079 | 0.971028 | 32.0 | 18.474361 |
| large_context_proxy | 131072 | remote_hbm | mqa | 4 | 2 | 56693.08 | qk_score | 0.601109 | 0.444079 | 0.971028 | 32.0 | 18.474361 |
| large_context_proxy | 131072 | remote_hbm | mqa | 4 | 4 | 56693.08 | qk_score | 0.601109 | 0.444079 | 0.971028 | 32.0 | 18.474361 |
| large_context_proxy | 131072 | shared_sram | gqa4 | 4 | 1 | 55711.0 | qk_score | 0.499952 | 0.888726 | 0.970501 | 256.0 | 3.728484 |
| large_context_proxy | 131072 | shared_sram | gqa4 | 4 | 2 | 109778.6 | qk_score | 0.507436 | 0.888726 | 0.98503 | 128.0 | 3.728484 |
| large_context_proxy | 131072 | shared_sram | gqa4 | 4 | 4 | 217913.8 | qk_score | 0.511263 | 0.888726 | 0.992458 | 64.0 | 3.728484 |
| large_context_proxy | 131072 | shared_sram | mqa | 4 | 1 | 8523.84 | qk_score | 0.499756 | 0.444079 | 0.807303 | 256.0 | 18.474361 |
| large_context_proxy | 131072 | shared_sram | mqa | 4 | 2 | 15405.16 | qk_score | 0.553041 | 0.444079 | 0.893379 | 128.0 | 18.474361 |
| large_context_proxy | 131072 | shared_sram | mqa | 4 | 4 | 29167.8 | qk_score | 0.584184 | 0.444079 | 0.943687 | 64.0 | 18.474361 |
| llama7b_proxy | 2048 | hbm | gqa4 | 4 | 1 | 2182.656 | qk_score | 0.510439 | 0.878593 | 0.991321 | 64.0 | 12.3003 |
| llama7b_proxy | 2048 | hbm | gqa4 | 4 | 2 | 2182.656 | qk_score | 0.510439 | 0.878593 | 0.991321 | 64.0 | 12.3003 |
| llama7b_proxy | 2048 | hbm | gqa4 | 4 | 4 | 2182.656 | qk_score | 0.510439 | 0.878593 | 0.991321 | 64.0 | 12.3003 |
| llama7b_proxy | 2048 | hbm | mqa | 4 | 1 | 346.304 | qk_score | 0.567732 | 0.477278 | 0.94659 | 64.0 | 46.773246 |
| llama7b_proxy | 2048 | hbm | mqa | 4 | 2 | 346.304 | qk_score | 0.567732 | 0.477278 | 0.94659 | 64.0 | 46.773246 |
| llama7b_proxy | 2048 | hbm | mqa | 4 | 4 | 346.304 | qk_score | 0.567732 | 0.477278 | 0.94659 | 64.0 | 46.773246 |
| llama7b_proxy | 2048 | remote_hbm | gqa4 | 4 | 1 | 4346.368 | qk_score | 0.512663 | 0.878593 | 0.995641 | 32.0 | 12.3003 |
| llama7b_proxy | 2048 | remote_hbm | gqa4 | 4 | 2 | 4346.368 | qk_score | 0.512663 | 0.878593 | 0.995641 | 32.0 | 12.3003 |
| llama7b_proxy | 2048 | remote_hbm | gqa4 | 4 | 4 | 4346.368 | qk_score | 0.512663 | 0.878593 | 0.995641 | 32.0 | 12.3003 |
| llama7b_proxy | 2048 | remote_hbm | mqa | 4 | 1 | 674.112 | qk_score | 0.58331 | 0.477278 | 0.972562 | 32.0 | 46.773246 |
| llama7b_proxy | 2048 | remote_hbm | mqa | 4 | 2 | 674.112 | qk_score | 0.58331 | 0.477278 | 0.972562 | 32.0 | 46.773246 |
| llama7b_proxy | 2048 | remote_hbm | mqa | 4 | 4 | 674.112 | qk_score | 0.58331 | 0.477278 | 0.972562 | 32.0 | 46.773246 |
| llama7b_proxy | 2048 | shared_sram | gqa4 | 4 | 1 | 559.872 | qk_score | 0.497485 | 0.878593 | 0.966164 | 256.0 | 12.3003 |
| llama7b_proxy | 2048 | shared_sram | gqa4 | 4 | 2 | 1100.8 | qk_score | 0.506047 | 0.878593 | 0.982791 | 128.0 | 12.3003 |
| llama7b_proxy | 2048 | shared_sram | gqa4 | 4 | 4 | 2182.656 | qk_score | 0.510439 | 0.878593 | 0.991321 | 64.0 | 12.3003 |
| llama7b_proxy | 2048 | shared_sram | mqa | 4 | 1 | 100.448 | qk_score | 0.489328 | 0.477278 | 0.815865 | 256.0 | 46.773246 |
| llama7b_proxy | 2048 | shared_sram | mqa | 4 | 2 | 182.4 | qk_score | 0.538947 | 0.477278 | 0.898596 | 128.0 | 46.773246 |
| llama7b_proxy | 2048 | shared_sram | mqa | 4 | 4 | 346.304 | qk_score | 0.567732 | 0.477278 | 0.94659 | 64.0 | 46.773246 |
| llama7b_proxy | 131072 | hbm | gqa4 | 4 | 1 | 139464.192 | qk_score | 0.511265 | 0.888726 | 0.992463 | 64.0 | 3.693768 |
| llama7b_proxy | 131072 | hbm | gqa4 | 4 | 2 | 139464.192 | qk_score | 0.511265 | 0.888726 | 0.992463 | 64.0 | 3.693768 |
| llama7b_proxy | 131072 | hbm | gqa4 | 4 | 4 | 139464.192 | qk_score | 0.511265 | 0.888726 | 0.992463 | 64.0 | 3.693768 |
| llama7b_proxy | 131072 | hbm | mqa | 4 | 1 | 22022.336 | qk_score | 0.57137 | 0.499628 | 0.95229 | 64.0 | 16.503349 |
| llama7b_proxy | 131072 | hbm | mqa | 4 | 2 | 22022.336 | qk_score | 0.57137 | 0.499628 | 0.95229 | 64.0 | 16.503349 |
| llama7b_proxy | 131072 | hbm | mqa | 4 | 4 | 22022.336 | qk_score | 0.57137 | 0.499628 | 0.95229 | 64.0 | 16.503349 |
| llama7b_proxy | 131072 | remote_hbm | gqa4 | 4 | 1 | 277877.248 | qk_score | 0.513199 | 0.888726 | 0.996217 | 32.0 | 3.693768 |
| llama7b_proxy | 131072 | remote_hbm | gqa4 | 4 | 2 | 277877.248 | qk_score | 0.513199 | 0.888726 | 0.996217 | 32.0 | 3.693768 |
| llama7b_proxy | 131072 | remote_hbm | gqa4 | 4 | 4 | 277877.248 | qk_score | 0.513199 | 0.888726 | 0.996217 | 32.0 | 3.693768 |
| llama7b_proxy | 131072 | remote_hbm | mqa | 4 | 1 | 42993.984 | qk_score | 0.585334 | 0.499628 | 0.975562 | 32.0 | 16.503349 |
| llama7b_proxy | 131072 | remote_hbm | mqa | 4 | 2 | 42993.984 | qk_score | 0.585334 | 0.499628 | 0.975562 | 32.0 | 16.503349 |
| llama7b_proxy | 131072 | remote_hbm | mqa | 4 | 4 | 42993.984 | qk_score | 0.585334 | 0.499628 | 0.975562 | 32.0 | 16.503349 |
| llama7b_proxy | 131072 | shared_sram | gqa4 | 4 | 1 | 35654.4 | qk_score | 0.499961 | 0.888726 | 0.970519 | 256.0 | 3.693768 |
| llama7b_proxy | 131072 | shared_sram | gqa4 | 4 | 2 | 70257.664 | qk_score | 0.50744 | 0.888726 | 0.985039 | 128.0 | 3.693768 |
| llama7b_proxy | 131072 | shared_sram | gqa4 | 4 | 4 | 139464.192 | qk_score | 0.511265 | 0.888726 | 0.992463 | 64.0 | 3.693768 |
| llama7b_proxy | 131072 | shared_sram | mqa | 4 | 1 | 6293.6 | qk_score | 0.49983 | 0.499628 | 0.833055 | 256.0 | 16.503349 |
| llama7b_proxy | 131072 | shared_sram | mqa | 4 | 2 | 11536.512 | qk_score | 0.545352 | 0.499628 | 0.908925 | 128.0 | 16.503349 |
| llama7b_proxy | 131072 | shared_sram | mqa | 4 | 4 | 22022.336 | qk_score | 0.57137 | 0.499628 | 0.95229 | 64.0 | 16.503349 |

## Assumptions

- This is an analytical single-token decode attention model, not measured RTL.
- Q/K/V projection, QK score, softmax, value mix, and attention output projection are separated.
- KV read traffic is charged to QK score and value mix; KV write traffic is charged once per token.
- KV memory tier bandwidths are planning values: local_sram=1024, shared_sram=256, hbm=64, remote_hbm=32 bytes/cycle.
- NoC contention is represented by effective KV bandwidth min(tier_bandwidth, noc_bandwidth / hops) for non-local tiers.
- GQA/MQA reduce KV-cache width but not query/output projection width.
- streaming_weights charges attention projection weights each token; resident_weights exposes KV and compute pressure.
