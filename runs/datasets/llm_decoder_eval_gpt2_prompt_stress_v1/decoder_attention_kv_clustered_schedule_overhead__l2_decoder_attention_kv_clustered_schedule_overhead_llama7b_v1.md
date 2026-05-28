# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `252720`
- skipped_area_budget_count: `0`

## Best

| seq | die | SRAM | logic | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 2 | owner_cluster | 1024 | 6.6331 | 14973.613005 | tile_attention |

## Best By Overhead

| die | cmd/tile | cmd/wave | reducer setup | reduction x | clusters | reduction | latency us | resource |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 400.0 | 0 | 0 | 0 | 1.0 | 4 | owner_cluster | 45221.82256 | tile_attention |
| 400.0 | 0 | 0 | 0 | 2.0 | 4 | owner_cluster | 45387.596995 | tile_attention |
| 400.0 | 0 | 0 | 0 | 4.0 | 1 | centralized_tile | 45719.145866 | cross_tile_reduction |
| 400.0 | 0 | 0 | 32 | 1.0 | 4 | owner_cluster | 45228.614854 | tile_attention |
| 400.0 | 0 | 0 | 32 | 2.0 | 4 | owner_cluster | 45394.38929 | tile_attention |
| 400.0 | 0 | 0 | 32 | 4.0 | 1 | centralized_tile | 45725.93816 | cross_tile_reduction |
| 400.0 | 0 | 0 | 128 | 1.0 | 4 | owner_cluster | 45248.991738 | tile_attention |
| 400.0 | 0 | 0 | 128 | 2.0 | 4 | owner_cluster | 45414.766173 | tile_attention |
| 400.0 | 0 | 0 | 128 | 4.0 | 1 | centralized_tile | 45746.315043 | cross_tile_reduction |
| 400.0 | 0 | 8 | 0 | 1.0 | 8 | owner_cluster | 45254.085958 | tile_attention |
| 400.0 | 0 | 8 | 0 | 2.0 | 8 | owner_cluster | 45424.954614 | tile_attention |
| 400.0 | 0 | 8 | 0 | 4.0 | 8 | owner_cluster | 45766.691926 | tile_attention |
| 400.0 | 0 | 8 | 32 | 1.0 | 8 | owner_cluster | 45260.878253 | tile_attention |
| 400.0 | 0 | 8 | 32 | 2.0 | 8 | owner_cluster | 45431.746909 | tile_attention |
| 400.0 | 0 | 8 | 32 | 4.0 | 8 | owner_cluster | 45773.484221 | tile_attention |
| 400.0 | 0 | 8 | 128 | 1.0 | 8 | owner_cluster | 45281.255136 | tile_attention |
| 400.0 | 0 | 8 | 128 | 2.0 | 8 | owner_cluster | 45452.123792 | tile_attention |
| 400.0 | 0 | 8 | 128 | 4.0 | 8 | owner_cluster | 45793.861104 | tile_attention |
| 400.0 | 0 | 32 | 0 | 1.0 | 8 | owner_cluster | 45335.593491 | tile_attention |
| 400.0 | 0 | 32 | 0 | 2.0 | 8 | owner_cluster | 45506.462147 | tile_attention |
| 400.0 | 0 | 32 | 0 | 4.0 | 8 | owner_cluster | 45848.199459 | tile_attention |
| 400.0 | 0 | 32 | 32 | 1.0 | 8 | owner_cluster | 45342.385786 | tile_attention |
| 400.0 | 0 | 32 | 32 | 2.0 | 8 | owner_cluster | 45513.254442 | tile_attention |
| 400.0 | 0 | 32 | 32 | 4.0 | 8 | owner_cluster | 45854.991754 | tile_attention |
| 400.0 | 0 | 32 | 128 | 1.0 | 8 | owner_cluster | 45362.762669 | tile_attention |
| 400.0 | 0 | 32 | 128 | 2.0 | 8 | owner_cluster | 45533.631325 | tile_attention |
| 400.0 | 0 | 32 | 128 | 4.0 | 8 | owner_cluster | 45875.368637 | tile_attention |
| 400.0 | 1 | 0 | 0 | 1.0 | 4 | owner_cluster | 45248.991738 | tile_attention |
| 400.0 | 1 | 0 | 0 | 2.0 | 4 | owner_cluster | 45414.766173 | tile_attention |
| 400.0 | 1 | 0 | 0 | 4.0 | 1 | centralized_tile | 45746.315043 | cross_tile_reduction |
| 400.0 | 1 | 0 | 32 | 1.0 | 4 | owner_cluster | 45255.784032 | tile_attention |
| 400.0 | 1 | 0 | 32 | 2.0 | 4 | owner_cluster | 45421.558467 | tile_attention |
| 400.0 | 1 | 0 | 32 | 4.0 | 1 | centralized_tile | 45753.107338 | cross_tile_reduction |
| 400.0 | 1 | 0 | 128 | 1.0 | 4 | owner_cluster | 45276.160915 | tile_attention |
| 400.0 | 1 | 0 | 128 | 2.0 | 4 | owner_cluster | 45441.93535 | tile_attention |
| 400.0 | 1 | 0 | 128 | 4.0 | 1 | centralized_tile | 45773.484221 | cross_tile_reduction |
| 400.0 | 1 | 8 | 0 | 1.0 | 8 | owner_cluster | 45281.255136 | tile_attention |
| 400.0 | 1 | 8 | 0 | 2.0 | 8 | owner_cluster | 45452.123792 | tile_attention |
| 400.0 | 1 | 8 | 0 | 4.0 | 8 | owner_cluster | 45793.861104 | tile_attention |
| 400.0 | 1 | 8 | 32 | 1.0 | 8 | owner_cluster | 45288.04743 | tile_attention |
| 400.0 | 1 | 8 | 32 | 2.0 | 8 | owner_cluster | 45458.916086 | tile_attention |
| 400.0 | 1 | 8 | 32 | 4.0 | 8 | owner_cluster | 45800.653398 | tile_attention |
| 400.0 | 1 | 8 | 128 | 1.0 | 8 | owner_cluster | 45308.424314 | tile_attention |
| 400.0 | 1 | 8 | 128 | 2.0 | 8 | owner_cluster | 45479.29297 | tile_attention |
| 400.0 | 1 | 8 | 128 | 4.0 | 8 | owner_cluster | 45821.030282 | tile_attention |
| 400.0 | 1 | 32 | 0 | 1.0 | 8 | owner_cluster | 45362.762669 | tile_attention |
| 400.0 | 1 | 32 | 0 | 2.0 | 8 | owner_cluster | 45533.631325 | tile_attention |
| 400.0 | 1 | 32 | 0 | 4.0 | 8 | owner_cluster | 45875.368637 | tile_attention |
| 400.0 | 1 | 32 | 32 | 1.0 | 8 | owner_cluster | 45369.554963 | tile_attention |
| 400.0 | 1 | 32 | 32 | 2.0 | 8 | owner_cluster | 45540.423619 | tile_attention |
| 400.0 | 1 | 32 | 32 | 4.0 | 8 | owner_cluster | 45882.160931 | tile_attention |
| 400.0 | 1 | 32 | 128 | 1.0 | 8 | owner_cluster | 45389.931846 | tile_attention |
| 400.0 | 1 | 32 | 128 | 2.0 | 8 | owner_cluster | 45560.800502 | tile_attention |
| 400.0 | 1 | 32 | 128 | 4.0 | 8 | owner_cluster | 45902.537814 | tile_attention |
| 400.0 | 4 | 0 | 0 | 1.0 | 4 | owner_cluster | 45330.49927 | tile_attention |
| 400.0 | 4 | 0 | 0 | 2.0 | 4 | owner_cluster | 45496.273706 | tile_attention |
| 400.0 | 4 | 0 | 0 | 4.0 | 1 | centralized_tile | 45827.822576 | cross_tile_reduction |
| 400.0 | 4 | 0 | 32 | 1.0 | 4 | owner_cluster | 45337.291565 | tile_attention |
| 400.0 | 4 | 0 | 32 | 2.0 | 4 | owner_cluster | 45503.066 | tile_attention |
| 400.0 | 4 | 0 | 32 | 4.0 | 1 | centralized_tile | 45834.61487 | cross_tile_reduction |
| 400.0 | 4 | 0 | 128 | 1.0 | 4 | owner_cluster | 45357.668448 | tile_attention |
| 400.0 | 4 | 0 | 128 | 2.0 | 4 | owner_cluster | 45523.442883 | tile_attention |
| 400.0 | 4 | 0 | 128 | 4.0 | 1 | centralized_tile | 45854.991754 | cross_tile_reduction |
| 400.0 | 4 | 8 | 0 | 1.0 | 8 | owner_cluster | 45362.762669 | tile_attention |
| 400.0 | 4 | 8 | 0 | 2.0 | 8 | owner_cluster | 45533.631325 | tile_attention |
| 400.0 | 4 | 8 | 0 | 4.0 | 8 | owner_cluster | 45875.368637 | tile_attention |
| 400.0 | 4 | 8 | 32 | 1.0 | 8 | owner_cluster | 45369.554963 | tile_attention |
| 400.0 | 4 | 8 | 32 | 2.0 | 8 | owner_cluster | 45540.423619 | tile_attention |
| 400.0 | 4 | 8 | 32 | 4.0 | 8 | owner_cluster | 45882.160931 | tile_attention |
| 400.0 | 4 | 8 | 128 | 1.0 | 8 | owner_cluster | 45389.931846 | tile_attention |
| 400.0 | 4 | 8 | 128 | 2.0 | 8 | owner_cluster | 45560.800502 | tile_attention |
| 400.0 | 4 | 8 | 128 | 4.0 | 8 | owner_cluster | 45902.537814 | tile_attention |
| 400.0 | 4 | 32 | 0 | 1.0 | 8 | owner_cluster | 45444.270202 | tile_attention |
| 400.0 | 4 | 32 | 0 | 2.0 | 8 | owner_cluster | 45615.138858 | tile_attention |
| 400.0 | 4 | 32 | 0 | 4.0 | 8 | owner_cluster | 45956.87617 | tile_attention |
| 400.0 | 4 | 32 | 32 | 1.0 | 8 | owner_cluster | 45451.062496 | tile_attention |
| 400.0 | 4 | 32 | 32 | 2.0 | 8 | owner_cluster | 45621.931152 | tile_attention |
| 400.0 | 4 | 32 | 32 | 4.0 | 8 | owner_cluster | 45963.668464 | tile_attention |
| 400.0 | 4 | 32 | 128 | 1.0 | 8 | owner_cluster | 45471.439379 | tile_attention |
| 400.0 | 4 | 32 | 128 | 2.0 | 8 | owner_cluster | 45642.308035 | tile_attention |
| 400.0 | 4 | 32 | 128 | 4.0 | 8 | owner_cluster | 45984.045347 | tile_attention |
| 400.0 | 16 | 0 | 0 | 1.0 | 4 | owner_cluster | 45656.529402 | tile_attention |
| 400.0 | 16 | 0 | 0 | 2.0 | 4 | owner_cluster | 45822.303837 | tile_attention |
| 400.0 | 16 | 0 | 0 | 4.0 | 1 | centralized_tile | 46153.852707 | cross_tile_reduction |
| 400.0 | 16 | 0 | 32 | 1.0 | 4 | owner_cluster | 45663.321696 | tile_attention |
| 400.0 | 16 | 0 | 32 | 2.0 | 4 | owner_cluster | 45829.096131 | tile_attention |
| 400.0 | 16 | 0 | 32 | 4.0 | 1 | centralized_tile | 46160.645002 | cross_tile_reduction |
| 400.0 | 16 | 0 | 128 | 1.0 | 4 | owner_cluster | 45683.698579 | tile_attention |
| 400.0 | 16 | 0 | 128 | 2.0 | 4 | owner_cluster | 45849.473014 | tile_attention |
| 400.0 | 16 | 0 | 128 | 4.0 | 1 | centralized_tile | 46181.021885 | cross_tile_reduction |
| 400.0 | 16 | 8 | 0 | 1.0 | 8 | owner_cluster | 45688.7928 | tile_attention |
| 400.0 | 16 | 8 | 0 | 2.0 | 8 | owner_cluster | 45859.661456 | tile_attention |
| 400.0 | 16 | 8 | 0 | 4.0 | 8 | owner_cluster | 46201.398768 | tile_attention |
| 400.0 | 16 | 8 | 32 | 1.0 | 8 | owner_cluster | 45695.585094 | tile_attention |
| 400.0 | 16 | 8 | 32 | 2.0 | 8 | owner_cluster | 45866.45375 | tile_attention |
| 400.0 | 16 | 8 | 32 | 4.0 | 8 | owner_cluster | 46208.191062 | tile_attention |
| 400.0 | 16 | 8 | 128 | 1.0 | 8 | owner_cluster | 45715.961978 | tile_attention |
| 400.0 | 16 | 8 | 128 | 2.0 | 8 | owner_cluster | 45886.830634 | tile_attention |
| 400.0 | 16 | 8 | 128 | 4.0 | 8 | owner_cluster | 46228.567946 | tile_attention |
| 400.0 | 16 | 32 | 0 | 1.0 | 8 | owner_cluster | 45770.300333 | tile_attention |
| 400.0 | 16 | 32 | 0 | 2.0 | 8 | owner_cluster | 45941.168989 | tile_attention |
| 400.0 | 16 | 32 | 0 | 4.0 | 8 | owner_cluster | 46282.906301 | tile_attention |
| 400.0 | 16 | 32 | 32 | 1.0 | 8 | owner_cluster | 45777.092627 | tile_attention |
| 400.0 | 16 | 32 | 32 | 2.0 | 8 | owner_cluster | 45947.961283 | tile_attention |
| 400.0 | 16 | 32 | 32 | 4.0 | 8 | owner_cluster | 46289.698595 | tile_attention |
| 400.0 | 16 | 32 | 128 | 1.0 | 8 | owner_cluster | 45797.46951 | tile_attention |
| 400.0 | 16 | 32 | 128 | 2.0 | 8 | owner_cluster | 45968.338166 | tile_attention |
| 400.0 | 16 | 32 | 128 | 4.0 | 8 | owner_cluster | 46310.075478 | tile_attention |
| 800.0 | 0 | 0 | 0 | 1.0 | 1 | centralized_tile | 22534.710227 | tile_attention |
| 800.0 | 0 | 0 | 0 | 2.0 | 1 | centralized_tile | 22614.731946 | tile_attention |
| 800.0 | 0 | 0 | 0 | 4.0 | 1 | centralized_tile | 22774.775382 | cross_tile_reduction |
| 800.0 | 0 | 0 | 32 | 1.0 | 1 | centralized_tile | 22541.502522 | tile_attention |
| 800.0 | 0 | 0 | 32 | 2.0 | 1 | centralized_tile | 22621.52424 | tile_attention |
| 800.0 | 0 | 0 | 32 | 4.0 | 1 | centralized_tile | 22781.567677 | cross_tile_reduction |
| 800.0 | 0 | 0 | 128 | 1.0 | 1 | centralized_tile | 22561.879405 | tile_attention |
| 800.0 | 0 | 0 | 128 | 2.0 | 1 | centralized_tile | 22641.901123 | cross_tile_reduction |
| 800.0 | 0 | 0 | 128 | 4.0 | 1 | centralized_tile | 22801.94456 | cross_tile_reduction |
| 800.0 | 0 | 8 | 0 | 1.0 | 16 | owner_cluster | 22630.226867 | tile_attention |
| 800.0 | 0 | 8 | 0 | 2.0 | 16 | owner_cluster | 22720.861546 | tile_attention |
| 800.0 | 0 | 8 | 0 | 4.0 | 8 | owner_cluster | 22895.338608 | tile_attention |
| 800.0 | 0 | 8 | 32 | 1.0 | 16 | owner_cluster | 22637.019162 | tile_attention |
| 800.0 | 0 | 8 | 32 | 2.0 | 16 | owner_cluster | 22727.65384 | tile_attention |
| 800.0 | 0 | 8 | 32 | 4.0 | 8 | owner_cluster | 22902.130902 | tile_attention |
| 800.0 | 0 | 8 | 128 | 1.0 | 16 | owner_cluster | 22657.396045 | tile_attention |
| 800.0 | 0 | 8 | 128 | 2.0 | 16 | owner_cluster | 22748.030723 | tile_attention |
| 800.0 | 0 | 8 | 128 | 4.0 | 8 | owner_cluster | 22922.507786 | tile_attention |
| 800.0 | 0 | 32 | 0 | 1.0 | 16 | owner_cluster | 22670.980634 | tile_attention |
| 800.0 | 0 | 32 | 0 | 2.0 | 16 | owner_cluster | 22761.615312 | tile_attention |
| 800.0 | 0 | 32 | 0 | 4.0 | 16 | owner_cluster | 22942.884669 | tile_attention |
| 800.0 | 0 | 32 | 32 | 1.0 | 16 | owner_cluster | 22677.772928 | tile_attention |
| 800.0 | 0 | 32 | 32 | 2.0 | 16 | owner_cluster | 22768.407606 | tile_attention |
| 800.0 | 0 | 32 | 32 | 4.0 | 16 | owner_cluster | 22949.676963 | tile_attention |
| 800.0 | 0 | 32 | 128 | 1.0 | 16 | owner_cluster | 22698.149811 | tile_attention |
| 800.0 | 0 | 32 | 128 | 2.0 | 16 | owner_cluster | 22788.78449 | tile_attention |
| 800.0 | 0 | 32 | 128 | 4.0 | 16 | owner_cluster | 22970.053846 | tile_attention |
| 800.0 | 1 | 0 | 0 | 1.0 | 1 | centralized_tile | 22561.879405 | tile_attention |
| 800.0 | 1 | 0 | 0 | 2.0 | 1 | centralized_tile | 22641.901123 | tile_attention |
| 800.0 | 1 | 0 | 0 | 4.0 | 1 | centralized_tile | 22801.94456 | cross_tile_reduction |
| 800.0 | 1 | 0 | 32 | 1.0 | 1 | centralized_tile | 22568.671699 | tile_attention |
| 800.0 | 1 | 0 | 32 | 2.0 | 1 | centralized_tile | 22648.693418 | tile_attention |
| 800.0 | 1 | 0 | 32 | 4.0 | 1 | centralized_tile | 22808.736854 | cross_tile_reduction |
| 800.0 | 1 | 0 | 128 | 1.0 | 1 | centralized_tile | 22589.048582 | tile_attention |
| 800.0 | 1 | 0 | 128 | 2.0 | 1 | centralized_tile | 22669.070301 | cross_tile_reduction |
| 800.0 | 1 | 0 | 128 | 4.0 | 1 | centralized_tile | 22829.113738 | cross_tile_reduction |
| 800.0 | 1 | 8 | 0 | 1.0 | 16 | owner_cluster | 22657.396045 | tile_attention |
| 800.0 | 1 | 8 | 0 | 2.0 | 16 | owner_cluster | 22748.030723 | tile_attention |
| 800.0 | 1 | 8 | 0 | 4.0 | 8 | owner_cluster | 22922.507786 | tile_attention |
| 800.0 | 1 | 8 | 32 | 1.0 | 16 | owner_cluster | 22664.188339 | tile_attention |
| 800.0 | 1 | 8 | 32 | 2.0 | 16 | owner_cluster | 22754.823018 | tile_attention |
| 800.0 | 1 | 8 | 32 | 4.0 | 8 | owner_cluster | 22929.30008 | tile_attention |
| 800.0 | 1 | 8 | 128 | 1.0 | 16 | owner_cluster | 22684.565222 | tile_attention |
| 800.0 | 1 | 8 | 128 | 2.0 | 16 | owner_cluster | 22775.199901 | tile_attention |
| 800.0 | 1 | 8 | 128 | 4.0 | 8 | owner_cluster | 22949.676963 | tile_attention |
| 800.0 | 1 | 32 | 0 | 1.0 | 16 | owner_cluster | 22698.149811 | tile_attention |
| 800.0 | 1 | 32 | 0 | 2.0 | 16 | owner_cluster | 22788.78449 | tile_attention |
| 800.0 | 1 | 32 | 0 | 4.0 | 16 | owner_cluster | 22970.053846 | tile_attention |
| 800.0 | 1 | 32 | 32 | 1.0 | 16 | owner_cluster | 22704.942106 | tile_attention |
| 800.0 | 1 | 32 | 32 | 2.0 | 16 | owner_cluster | 22795.576784 | tile_attention |
| 800.0 | 1 | 32 | 32 | 4.0 | 16 | owner_cluster | 22976.846141 | tile_attention |
| 800.0 | 1 | 32 | 128 | 1.0 | 16 | owner_cluster | 22725.318989 | tile_attention |
| 800.0 | 1 | 32 | 128 | 2.0 | 16 | owner_cluster | 22815.953667 | tile_attention |
| 800.0 | 1 | 32 | 128 | 4.0 | 16 | owner_cluster | 22997.223024 | tile_attention |
| 800.0 | 4 | 0 | 0 | 1.0 | 1 | centralized_tile | 22643.386938 | tile_attention |
| 800.0 | 4 | 0 | 0 | 2.0 | 1 | centralized_tile | 22723.408656 | tile_attention |
| 800.0 | 4 | 0 | 0 | 4.0 | 1 | centralized_tile | 22883.452093 | cross_tile_reduction |
| 800.0 | 4 | 0 | 32 | 1.0 | 1 | centralized_tile | 22650.179232 | tile_attention |
| 800.0 | 4 | 0 | 32 | 2.0 | 1 | centralized_tile | 22730.20095 | tile_attention |
| 800.0 | 4 | 0 | 32 | 4.0 | 1 | centralized_tile | 22890.244387 | cross_tile_reduction |
| 800.0 | 4 | 0 | 128 | 1.0 | 1 | centralized_tile | 22670.556115 | tile_attention |
| 800.0 | 4 | 0 | 128 | 2.0 | 1 | centralized_tile | 22750.577834 | cross_tile_reduction |
| 800.0 | 4 | 0 | 128 | 4.0 | 1 | centralized_tile | 22910.62127 | cross_tile_reduction |
| 800.0 | 4 | 8 | 0 | 1.0 | 16 | owner_cluster | 22738.903578 | tile_attention |
| 800.0 | 4 | 8 | 0 | 2.0 | 16 | owner_cluster | 22829.538256 | tile_attention |
| 800.0 | 4 | 8 | 0 | 4.0 | 8 | owner_cluster | 23004.015318 | tile_attention |
| 800.0 | 4 | 8 | 32 | 1.0 | 16 | owner_cluster | 22745.695872 | tile_attention |
| 800.0 | 4 | 8 | 32 | 2.0 | 16 | owner_cluster | 22836.33055 | tile_attention |
| 800.0 | 4 | 8 | 32 | 4.0 | 8 | owner_cluster | 23010.807613 | tile_attention |
| 800.0 | 4 | 8 | 128 | 1.0 | 16 | owner_cluster | 22766.072755 | tile_attention |
| 800.0 | 4 | 8 | 128 | 2.0 | 16 | owner_cluster | 22856.707434 | tile_attention |
| 800.0 | 4 | 8 | 128 | 4.0 | 8 | owner_cluster | 23031.184496 | tile_attention |
| 800.0 | 4 | 32 | 0 | 1.0 | 16 | owner_cluster | 22779.657344 | tile_attention |
| 800.0 | 4 | 32 | 0 | 2.0 | 16 | owner_cluster | 22870.292022 | tile_attention |
| 800.0 | 4 | 32 | 0 | 4.0 | 16 | owner_cluster | 23051.561379 | tile_attention |
| 800.0 | 4 | 32 | 32 | 1.0 | 16 | owner_cluster | 22786.449638 | tile_attention |
| 800.0 | 4 | 32 | 32 | 2.0 | 16 | owner_cluster | 22877.084317 | tile_attention |
| 800.0 | 4 | 32 | 32 | 4.0 | 16 | owner_cluster | 23058.353674 | tile_attention |
| 800.0 | 4 | 32 | 128 | 1.0 | 16 | owner_cluster | 22806.826522 | tile_attention |
| 800.0 | 4 | 32 | 128 | 2.0 | 16 | owner_cluster | 22897.4612 | tile_attention |
| 800.0 | 4 | 32 | 128 | 4.0 | 16 | owner_cluster | 23078.730557 | tile_attention |
| 800.0 | 16 | 0 | 0 | 1.0 | 1 | centralized_tile | 22969.417069 | command_dispatch |
| 800.0 | 16 | 0 | 0 | 2.0 | 1 | centralized_tile | 23049.438787 | command_dispatch |
| 800.0 | 16 | 0 | 0 | 4.0 | 1 | centralized_tile | 23209.482224 | command_dispatch |
| 800.0 | 16 | 0 | 32 | 1.0 | 1 | centralized_tile | 22976.209363 | command_dispatch |
| 800.0 | 16 | 0 | 32 | 2.0 | 1 | centralized_tile | 23056.231082 | command_dispatch |
| 800.0 | 16 | 0 | 32 | 4.0 | 1 | centralized_tile | 23216.274518 | command_dispatch |
| 800.0 | 16 | 0 | 128 | 1.0 | 1 | centralized_tile | 22996.586246 | command_dispatch |
| 800.0 | 16 | 0 | 128 | 2.0 | 1 | centralized_tile | 23076.607965 | command_dispatch |
| 800.0 | 16 | 0 | 128 | 4.0 | 1 | centralized_tile | 23236.651402 | command_dispatch |
| 800.0 | 16 | 8 | 0 | 1.0 | 16 | owner_cluster | 23064.933709 | tile_attention |
| 800.0 | 16 | 8 | 0 | 2.0 | 16 | owner_cluster | 23155.568387 | tile_attention |
| 800.0 | 16 | 8 | 0 | 4.0 | 8 | owner_cluster | 23330.04545 | tile_attention |
| 800.0 | 16 | 8 | 32 | 1.0 | 16 | owner_cluster | 23071.726003 | tile_attention |
| 800.0 | 16 | 8 | 32 | 2.0 | 16 | owner_cluster | 23162.360682 | tile_attention |
| 800.0 | 16 | 8 | 32 | 4.0 | 8 | owner_cluster | 23336.837744 | tile_attention |
| 800.0 | 16 | 8 | 128 | 1.0 | 16 | owner_cluster | 23092.102886 | tile_attention |
| 800.0 | 16 | 8 | 128 | 2.0 | 16 | owner_cluster | 23182.737565 | tile_attention |
| 800.0 | 16 | 8 | 128 | 4.0 | 8 | owner_cluster | 23357.214627 | tile_attention |
| 800.0 | 16 | 32 | 0 | 1.0 | 16 | owner_cluster | 23105.687475 | tile_attention |
| 800.0 | 16 | 32 | 0 | 2.0 | 16 | owner_cluster | 23196.322154 | tile_attention |
| 800.0 | 16 | 32 | 0 | 4.0 | 16 | owner_cluster | 23377.59151 | tile_attention |
| 800.0 | 16 | 32 | 32 | 1.0 | 16 | owner_cluster | 23112.47977 | tile_attention |
| 800.0 | 16 | 32 | 32 | 2.0 | 16 | owner_cluster | 23203.114448 | tile_attention |
| 800.0 | 16 | 32 | 32 | 4.0 | 16 | owner_cluster | 23384.383805 | tile_attention |
| 800.0 | 16 | 32 | 128 | 1.0 | 16 | owner_cluster | 23132.856653 | tile_attention |
| 800.0 | 16 | 32 | 128 | 2.0 | 16 | owner_cluster | 23223.491331 | tile_attention |
| 800.0 | 16 | 32 | 128 | 4.0 | 16 | owner_cluster | 23404.760688 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 1.0 | 2 | owner_cluster | 14973.613005 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 2.0 | 2 | owner_cluster | 15027.739101 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 4.0 | 2 | owner_cluster | 15135.991293 | tile_attention |
| 1200.0 | 0 | 0 | 32 | 1.0 | 2 | owner_cluster | 14980.405299 | tile_attention |
| 1200.0 | 0 | 0 | 32 | 2.0 | 2 | owner_cluster | 15034.531395 | tile_attention |
| 1200.0 | 0 | 0 | 32 | 4.0 | 2 | owner_cluster | 15142.783587 | tile_attention |
| 1200.0 | 0 | 0 | 128 | 1.0 | 2 | owner_cluster | 15000.782182 | tile_attention |
| 1200.0 | 0 | 0 | 128 | 2.0 | 2 | owner_cluster | 15054.908278 | tile_attention |
| 1200.0 | 0 | 0 | 128 | 4.0 | 2 | owner_cluster | 15163.16047 | cross_tile_reduction |
| 1200.0 | 0 | 8 | 0 | 1.0 | 2 | owner_cluster | 15082.289715 | tile_attention |
| 1200.0 | 0 | 8 | 0 | 2.0 | 2 | owner_cluster | 15136.415811 | tile_attention |
| 1200.0 | 0 | 8 | 0 | 4.0 | 2 | owner_cluster | 15244.668003 | tile_attention |
| 1200.0 | 0 | 8 | 32 | 1.0 | 2 | owner_cluster | 15089.08201 | tile_attention |
| 1200.0 | 0 | 8 | 32 | 2.0 | 2 | owner_cluster | 15143.208106 | tile_attention |
| 1200.0 | 0 | 8 | 32 | 4.0 | 2 | owner_cluster | 15251.460298 | tile_attention |
| 1200.0 | 0 | 8 | 128 | 1.0 | 2 | owner_cluster | 15109.458893 | tile_attention |
| 1200.0 | 0 | 8 | 128 | 2.0 | 2 | owner_cluster | 15163.584989 | tile_attention |
| 1200.0 | 0 | 8 | 128 | 4.0 | 2 | owner_cluster | 15271.837181 | cross_tile_reduction |
| 1200.0 | 0 | 32 | 0 | 1.0 | 8 | cluster_tree | 15183.749613 | tile_attention |
| 1200.0 | 0 | 32 | 0 | 2.0 | 8 | cluster_tree | 15240.847338 | tile_attention |
| 1200.0 | 0 | 32 | 0 | 4.0 | 8 | cluster_tree | 15355.042787 | tile_attention |
| 1200.0 | 0 | 32 | 32 | 1.0 | 8 | cluster_tree | 15190.541907 | tile_attention |
| 1200.0 | 0 | 32 | 32 | 2.0 | 8 | cluster_tree | 15247.639632 | tile_attention |
| 1200.0 | 0 | 32 | 32 | 4.0 | 8 | cluster_tree | 15361.835082 | tile_attention |
| 1200.0 | 0 | 32 | 128 | 1.0 | 8 | cluster_tree | 15210.91879 | tile_attention |
| 1200.0 | 0 | 32 | 128 | 2.0 | 8 | cluster_tree | 15268.016515 | tile_attention |
| 1200.0 | 0 | 32 | 128 | 4.0 | 8 | cluster_tree | 15382.211965 | tile_attention |
| 1200.0 | 1 | 0 | 0 | 1.0 | 2 | owner_cluster | 15000.782182 | tile_attention |
| 1200.0 | 1 | 0 | 0 | 2.0 | 2 | owner_cluster | 15054.908278 | tile_attention |
| 1200.0 | 1 | 0 | 0 | 4.0 | 2 | owner_cluster | 15163.16047 | tile_attention |
| 1200.0 | 1 | 0 | 32 | 1.0 | 2 | owner_cluster | 15007.574477 | tile_attention |
| 1200.0 | 1 | 0 | 32 | 2.0 | 2 | owner_cluster | 15061.700573 | tile_attention |
| 1200.0 | 1 | 0 | 32 | 4.0 | 2 | owner_cluster | 15169.952765 | tile_attention |
| 1200.0 | 1 | 0 | 128 | 1.0 | 2 | owner_cluster | 15027.95136 | tile_attention |
| 1200.0 | 1 | 0 | 128 | 2.0 | 2 | owner_cluster | 15082.077456 | tile_attention |
| 1200.0 | 1 | 0 | 128 | 4.0 | 2 | owner_cluster | 15190.329648 | cross_tile_reduction |
| 1200.0 | 1 | 8 | 0 | 1.0 | 2 | owner_cluster | 15109.458893 | tile_attention |
| 1200.0 | 1 | 8 | 0 | 2.0 | 2 | owner_cluster | 15163.584989 | tile_attention |
| 1200.0 | 1 | 8 | 0 | 4.0 | 2 | owner_cluster | 15271.837181 | tile_attention |
| 1200.0 | 1 | 8 | 32 | 1.0 | 2 | owner_cluster | 15116.251187 | tile_attention |
| 1200.0 | 1 | 8 | 32 | 2.0 | 2 | owner_cluster | 15170.377283 | tile_attention |
| 1200.0 | 1 | 8 | 32 | 4.0 | 2 | owner_cluster | 15278.629475 | tile_attention |
| 1200.0 | 1 | 8 | 128 | 1.0 | 2 | owner_cluster | 15136.62807 | tile_attention |
| 1200.0 | 1 | 8 | 128 | 2.0 | 2 | owner_cluster | 15190.754166 | tile_attention |
| 1200.0 | 1 | 8 | 128 | 4.0 | 2 | owner_cluster | 15299.006358 | cross_tile_reduction |
| 1200.0 | 1 | 32 | 0 | 1.0 | 8 | cluster_tree | 15210.91879 | tile_attention |
| 1200.0 | 1 | 32 | 0 | 2.0 | 8 | cluster_tree | 15268.016515 | tile_attention |
| 1200.0 | 1 | 32 | 0 | 4.0 | 8 | cluster_tree | 15382.211965 | tile_attention |
| 1200.0 | 1 | 32 | 32 | 1.0 | 8 | cluster_tree | 15217.711085 | tile_attention |
| 1200.0 | 1 | 32 | 32 | 2.0 | 8 | cluster_tree | 15274.80881 | tile_attention |
| 1200.0 | 1 | 32 | 32 | 4.0 | 8 | cluster_tree | 15389.004259 | tile_attention |
| 1200.0 | 1 | 32 | 128 | 1.0 | 8 | cluster_tree | 15238.087968 | tile_attention |
| 1200.0 | 1 | 32 | 128 | 2.0 | 8 | cluster_tree | 15295.185693 | tile_attention |
| 1200.0 | 1 | 32 | 128 | 4.0 | 8 | cluster_tree | 15409.381142 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 1.0 | 2 | owner_cluster | 15082.289715 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 2.0 | 2 | owner_cluster | 15136.415811 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 4.0 | 2 | owner_cluster | 15244.668003 | tile_attention |
| 1200.0 | 4 | 0 | 32 | 1.0 | 2 | owner_cluster | 15089.08201 | tile_attention |
| 1200.0 | 4 | 0 | 32 | 2.0 | 2 | owner_cluster | 15143.208106 | tile_attention |
| 1200.0 | 4 | 0 | 32 | 4.0 | 2 | owner_cluster | 15251.460298 | tile_attention |
| 1200.0 | 4 | 0 | 128 | 1.0 | 2 | owner_cluster | 15109.458893 | tile_attention |
| 1200.0 | 4 | 0 | 128 | 2.0 | 2 | owner_cluster | 15163.584989 | tile_attention |
| 1200.0 | 4 | 0 | 128 | 4.0 | 2 | owner_cluster | 15271.837181 | cross_tile_reduction |
| 1200.0 | 4 | 8 | 0 | 1.0 | 2 | owner_cluster | 15190.966426 | tile_attention |
| 1200.0 | 4 | 8 | 0 | 2.0 | 2 | owner_cluster | 15245.092522 | tile_attention |
| 1200.0 | 4 | 8 | 0 | 4.0 | 2 | owner_cluster | 15353.344714 | tile_attention |
| 1200.0 | 4 | 8 | 32 | 1.0 | 2 | owner_cluster | 15197.75872 | tile_attention |
| 1200.0 | 4 | 8 | 32 | 2.0 | 2 | owner_cluster | 15251.884816 | tile_attention |
| 1200.0 | 4 | 8 | 32 | 4.0 | 2 | owner_cluster | 15360.137008 | tile_attention |
| 1200.0 | 4 | 8 | 128 | 1.0 | 2 | owner_cluster | 15218.135603 | tile_attention |
| 1200.0 | 4 | 8 | 128 | 2.0 | 2 | owner_cluster | 15272.261699 | tile_attention |
| 1200.0 | 4 | 8 | 128 | 4.0 | 2 | owner_cluster | 15380.513891 | cross_tile_reduction |
| 1200.0 | 4 | 32 | 0 | 1.0 | 8 | cluster_tree | 15292.426323 | tile_attention |
| 1200.0 | 4 | 32 | 0 | 2.0 | 8 | cluster_tree | 15349.524048 | tile_attention |
| 1200.0 | 4 | 32 | 0 | 4.0 | 8 | cluster_tree | 15463.719498 | tile_attention |
| 1200.0 | 4 | 32 | 32 | 1.0 | 8 | cluster_tree | 15299.218618 | tile_attention |
| 1200.0 | 4 | 32 | 32 | 2.0 | 8 | cluster_tree | 15356.316342 | tile_attention |
| 1200.0 | 4 | 32 | 32 | 4.0 | 8 | cluster_tree | 15470.511792 | tile_attention |
| 1200.0 | 4 | 32 | 128 | 1.0 | 8 | cluster_tree | 15319.595501 | tile_attention |
| 1200.0 | 4 | 32 | 128 | 2.0 | 8 | cluster_tree | 15376.693226 | tile_attention |
| 1200.0 | 4 | 32 | 128 | 4.0 | 8 | cluster_tree | 15490.888675 | tile_attention |
| 1200.0 | 16 | 0 | 0 | 1.0 | 2 | owner_cluster | 15408.319846 | command_dispatch |
| 1200.0 | 16 | 0 | 0 | 2.0 | 2 | owner_cluster | 15462.445942 | command_dispatch |
| 1200.0 | 16 | 0 | 0 | 4.0 | 2 | owner_cluster | 15570.698134 | command_dispatch |
| 1200.0 | 16 | 0 | 32 | 1.0 | 2 | owner_cluster | 15415.112141 | command_dispatch |
| 1200.0 | 16 | 0 | 32 | 2.0 | 2 | owner_cluster | 15469.238237 | command_dispatch |
| 1200.0 | 16 | 0 | 32 | 4.0 | 2 | owner_cluster | 15577.490429 | command_dispatch |
| 1200.0 | 16 | 0 | 128 | 1.0 | 2 | owner_cluster | 15435.489024 | command_dispatch |
| 1200.0 | 16 | 0 | 128 | 2.0 | 2 | owner_cluster | 15489.61512 | command_dispatch |
| 1200.0 | 16 | 0 | 128 | 4.0 | 2 | owner_cluster | 15597.867312 | command_dispatch |
| 1200.0 | 16 | 8 | 0 | 1.0 | 2 | owner_cluster | 15516.996557 | command_dispatch |
| 1200.0 | 16 | 8 | 0 | 2.0 | 2 | owner_cluster | 15571.122653 | command_dispatch |
| 1200.0 | 16 | 8 | 0 | 4.0 | 2 | owner_cluster | 15679.374845 | command_dispatch |
| 1200.0 | 16 | 8 | 32 | 1.0 | 2 | owner_cluster | 15523.788851 | command_dispatch |
| 1200.0 | 16 | 8 | 32 | 2.0 | 2 | owner_cluster | 15577.914947 | command_dispatch |
| 1200.0 | 16 | 8 | 32 | 4.0 | 2 | owner_cluster | 15686.167139 | command_dispatch |
| 1200.0 | 16 | 8 | 128 | 1.0 | 2 | owner_cluster | 15544.165734 | command_dispatch |
| 1200.0 | 16 | 8 | 128 | 2.0 | 2 | owner_cluster | 15598.29183 | command_dispatch |
| 1200.0 | 16 | 8 | 128 | 4.0 | 2 | owner_cluster | 15706.544022 | command_dispatch |
| 1200.0 | 16 | 32 | 0 | 1.0 | 8 | cluster_tree | 15618.456454 | tile_attention |
| 1200.0 | 16 | 32 | 0 | 2.0 | 8 | cluster_tree | 15675.554179 | tile_attention |
| 1200.0 | 16 | 32 | 0 | 4.0 | 8 | cluster_tree | 15789.749629 | tile_attention |
| 1200.0 | 16 | 32 | 32 | 1.0 | 8 | cluster_tree | 15625.248749 | tile_attention |
| 1200.0 | 16 | 32 | 32 | 2.0 | 8 | cluster_tree | 15682.346474 | tile_attention |
| 1200.0 | 16 | 32 | 32 | 4.0 | 8 | cluster_tree | 15796.541923 | tile_attention |
| 1200.0 | 16 | 32 | 128 | 1.0 | 8 | cluster_tree | 15645.625632 | tile_attention |
| 1200.0 | 16 | 32 | 128 | 2.0 | 8 | cluster_tree | 15702.723357 | tile_attention |
| 1200.0 | 16 | 32 | 128 | 4.0 | 8 | cluster_tree | 15816.918806 | tile_attention |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 400.0 | 1 | nm64_flat | 88 | centralized_tile | 128 | 1630 | 757 | 45237.105222 | tile_attention |
| 400.0 | 2 | nm64_flat | 88 | owner_cluster | 64 | 3260 | 769 | 45239.652333 | tile_attention |
| 400.0 | 4 | nm64_flat | 88 | owner_cluster | 32 | 6517 | 781 | 45221.82256 | tile_attention |
| 400.0 | 8 | nm64_flat | 88 | owner_cluster | 16 | 13034 | 805 | 45226.916781 | tile_attention |
| 400.0 | 16 | nm64_flat | 88 | owner_cluster | 8 | 28674 | 927 | 49677.992205 | tile_attention |
| 800.0 | 1 | nm64_flat | 177 | centralized_tile | 128 | 812 | 377 | 22534.710227 | tile_attention |
| 800.0 | 2 | nm64_flat | 177 | owner_cluster | 64 | 1630 | 385 | 22617.915834 | tile_attention |
| 800.0 | 4 | nm64_flat | 177 | owner_cluster | 32 | 3260 | 391 | 22619.189389 | tile_attention |
| 800.0 | 8 | nm64_flat | 177 | owner_cluster | 16 | 6517 | 403 | 22611.548058 | tile_attention |
| 800.0 | 16 | nm64_flat | 177 | owner_cluster | 8 | 13034 | 427 | 22616.642278 | tile_attention |
| 1200.0 | 1 | nm64_flat | 266 | centralized_tile | 128 | 541 | 251 | 15013.517734 | tile_attention |
| 1200.0 | 2 | nm64_flat | 266 | owner_cluster | 64 | 1079 | 255 | 14973.613005 | tile_attention |
| 1200.0 | 4 | nm64_flat | 266 | owner_cluster | 32 | 2173 | 261 | 15076.770976 | tile_attention |
| 1200.0 | 8 | nm64_flat | 266 | cluster_tree | 16 | 4345 | 269 | 15075.072902 | tile_attention |
| 1200.0 | 16 | nm64_flat | 266 | cluster_tree | 8 | 8960 | 292 | 15538.434736 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
- Optional command and reducer overhead parameters are sensitivity knobs, not measured RTL/PPA.
