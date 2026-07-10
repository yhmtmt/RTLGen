# Hierarchical Attention Composition Probe

- decision: `two_pass_exact_selected`
- online pass: `False`
- Llama7B score buffer MiB: `16.0`

| length | distribution | architecture | max value error q16 | exp-sum relative error |
|---:|---|---|---:|---:|
| 128 | normal_std1 | online_streaming | 1140 | 8.04056016e-06 |
| 128 | normal_std1 | online_balanced | 1769 | 5.36037344e-06 |
| 128 | normal_std1 | two_pass_global_max | 0 | 0 |
| 128 | normal_std4 | online_streaming | 9099 | 0.00206534835 |
| 128 | normal_std4 | online_balanced | 9111 | 0.00206534835 |
| 128 | normal_std4 | two_pass_global_max | 0 | 0 |
| 128 | monotonic_ramp16 | online_streaming | 806 | 0.000310873337 |
| 128 | monotonic_ramp16 | online_balanced | 48 | 3.61480625e-06 |
| 128 | monotonic_ramp16 | two_pass_global_max | 0 | 0 |
| 4096 | normal_std1 | online_streaming | 504 | 0.0011038145 |
| 4096 | normal_std1 | online_balanced | 488 | 0.0011289305 |
| 4096 | normal_std1 | two_pass_global_max | 0 | 0 |
| 4096 | normal_std4 | online_streaming | 35636 | 0.0147049871 |
| 4096 | normal_std4 | online_balanced | 41448 | 0.0166496439 |
| 4096 | normal_std4 | two_pass_global_max | 0 | 0 |
| 4096 | monotonic_ramp16 | online_streaming | 148 | 0.000331227979 |
| 4096 | monotonic_ramp16 | online_balanced | 6 | 3.09447626e-06 |
| 4096 | monotonic_ramp16 | two_pass_global_max | 0 | 0 |
| 131072 | normal_std1 | online_streaming | 45 | 0.000465147182 |
| 131072 | normal_std1 | online_balanced | 161 | 0.00140674439 |
| 131072 | normal_std1 | two_pass_global_max | 0 | 0 |
| 131072 | normal_std4 | online_streaming | 14566 | 0.0110592052 |
| 131072 | normal_std4 | online_balanced | 61734 | 0.0531904064 |
| 131072 | normal_std4 | two_pass_global_max | 0 | 0 |
| 131072 | monotonic_ramp16 | online_streaming | 67531 | 15.0053133 |
| 131072 | monotonic_ramp16 | online_balanced | 40 | 0.000333072785 |
| 131072 | monotonic_ramp16 | two_pass_global_max | 0 | 0 |
