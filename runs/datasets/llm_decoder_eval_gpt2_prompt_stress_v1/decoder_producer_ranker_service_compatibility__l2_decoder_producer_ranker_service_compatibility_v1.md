# Decoder Producer/Ranker Service Compatibility

- decision: `serial_ranker_service_compatible`
- lowest_power_feasible: `serial_lpc1 single_r64_ranker W64 II1536 service65`
- latency_best: `ranktree_radix8 banked_r64_rankers W128 301.068us`

## Compatibility Sweep

| ranker | integration | vocab | hidden | W | MAC/cycle | BW | prod II | service | margin | util | ok | extra cycles | power mW | placed area |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 1 | 1535 | 0.000651 | `True` | 7 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 1 | 1535 | 0.000651 | `True` | 4 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 1 | 1535 | 0.000651 | `True` | 3 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 65 | 1471 | 0.042318 | `True` | 65 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 5 | 1531 | 0.003255 | `True` | 5 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 33 | 1503 | 0.021484 | `True` | 33 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 17 | 1519 | 0.011068 | `True` | 17 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 64.0 | 1536 | 9 | 1527 | 0.005859 | `True` | 9 | 0.014957 | 20013.574 |
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 1 | 383 | 0.002604 | `True` | 7 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 1 | 383 | 0.002604 | `True` | 4 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 1 | 383 | 0.002604 | `True` | 3 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 65 | 319 | 0.169271 | `True` | 65 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 5 | 379 | 0.013021 | `True` | 5 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 33 | 351 | 0.085938 | `True` | 33 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 17 | 367 | 0.044271 | `True` | 17 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 64 | 8192 | 256.0 | 384 | 9 | 375 | 0.023438 | `True` | 9 | 0.014957 | 20013.574 |
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 1 | 1535 | 0.000651 | `True` | 7 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 1 | 1535 | 0.000651 | `True` | 4 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 1 | 1535 | 0.000651 | `True` | 3 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 65 | 1471 | 0.042318 | `True` | 65 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 5 | 1531 | 0.003255 | `True` | 5 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 33 | 1503 | 0.021484 | `True` | 33 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 17 | 1519 | 0.011068 | `True` | 17 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 64.0 | 1536 | 9 | 1527 | 0.005859 | `True` | 9 | 0.014957 | 20013.574 |
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 1 | 383 | 0.002604 | `True` | 7 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 1 | 383 | 0.002604 | `True` | 4 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 1 | 383 | 0.002604 | `True` | 3 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 65 | 319 | 0.169271 | `True` | 65 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 5 | 379 | 0.013021 | `True` | 5 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 33 | 351 | 0.085938 | `True` | 33 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 17 | 367 | 0.044271 | `True` | 17 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 64 | 32768 | 256.0 | 384 | 9 | 375 | 0.023438 | `True` | 9 | 0.014957 | 20013.574 |
| ranktree_radix2 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 1 | 3071 | 0.000326 | `True` | 7 | 0.0301216 | 67966.192 |
| ranktree_radix4 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 1 | 3071 | 0.000326 | `True` | 4 | 0.0228612 | 48904.632 |
| ranktree_radix8 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 1 | 3071 | 0.000326 | `True` | 3 | 0.0312206 | 45890.852 |
| serial_lpc1 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 65 | 3007 | 0.021159 | `True` | 65 | 0.0131038 | 38609.368 |
| serial_lpc16 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 5 | 3067 | 0.001628 | `True` | 5 | 0.1685208 | 42361.032 |
| serial_lpc2 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 33 | 3039 | 0.010742 | `True` | 33 | 0.0151134 | 39171.16 |
| serial_lpc4 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 17 | 3055 | 0.005534 | `True` | 17 | 0.0219634 | 39909.044 |
| serial_lpc8 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 9 | 3063 | 0.00293 | `True` | 9 | 0.029914 | 40027.148 |
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 2 | 3070 | 0.000651 | `True` | 8 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 2 | 3070 | 0.000651 | `True` | 5 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 2 | 3070 | 0.000651 | `True` | 4 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 130 | 2942 | 0.042318 | `True` | 130 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 10 | 3062 | 0.003255 | `True` | 10 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 66 | 3006 | 0.021484 | `True` | 66 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 34 | 3038 | 0.011068 | `True` | 34 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 64.0 | 3072 | 18 | 3054 | 0.005859 | `True` | 18 | 0.014957 | 20013.574 |
| ranktree_radix2 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 1 | 767 | 0.001302 | `True` | 7 | 0.0301216 | 67966.192 |
| ranktree_radix4 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 1 | 767 | 0.001302 | `True` | 4 | 0.0228612 | 48904.632 |
| ranktree_radix8 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 1 | 767 | 0.001302 | `True` | 3 | 0.0312206 | 45890.852 |
| serial_lpc1 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 65 | 703 | 0.084635 | `True` | 65 | 0.0131038 | 38609.368 |
| serial_lpc16 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 5 | 763 | 0.00651 | `True` | 5 | 0.1685208 | 42361.032 |
| serial_lpc2 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 33 | 735 | 0.042969 | `True` | 33 | 0.0151134 | 39171.16 |
| serial_lpc4 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 17 | 751 | 0.022135 | `True` | 17 | 0.0219634 | 39909.044 |
| serial_lpc8 | banked_r64_rankers | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 9 | 759 | 0.011719 | `True` | 9 | 0.029914 | 40027.148 |
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 2 | 766 | 0.002604 | `True` | 8 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 2 | 766 | 0.002604 | `True` | 5 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 2 | 766 | 0.002604 | `True` | 4 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 130 | 638 | 0.169271 | `True` | 130 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 10 | 758 | 0.013021 | `True` | 10 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 66 | 702 | 0.085938 | `True` | 66 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 34 | 734 | 0.044271 | `True` | 34 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 128 | 8192 | 256.0 | 768 | 18 | 750 | 0.023438 | `True` | 18 | 0.014957 | 20013.574 |
| ranktree_radix2 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 1 | 3071 | 0.000326 | `True` | 7 | 0.0301216 | 67966.192 |
| ranktree_radix4 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 1 | 3071 | 0.000326 | `True` | 4 | 0.0228612 | 48904.632 |
| ranktree_radix8 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 1 | 3071 | 0.000326 | `True` | 3 | 0.0312206 | 45890.852 |
| serial_lpc1 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 65 | 3007 | 0.021159 | `True` | 65 | 0.0131038 | 38609.368 |
| serial_lpc16 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 5 | 3067 | 0.001628 | `True` | 5 | 0.1685208 | 42361.032 |
| serial_lpc2 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 33 | 3039 | 0.010742 | `True` | 33 | 0.0151134 | 39171.16 |
| serial_lpc4 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 17 | 3055 | 0.005534 | `True` | 17 | 0.0219634 | 39909.044 |
| serial_lpc8 | banked_r64_rankers | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 9 | 3063 | 0.00293 | `True` | 9 | 0.029914 | 40027.148 |
| ranktree_radix2 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 2 | 3070 | 0.000651 | `True` | 8 | 0.0150608 | 33983.096 |
| ranktree_radix4 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 2 | 3070 | 0.000651 | `True` | 5 | 0.0114306 | 24452.316 |
| ranktree_radix8 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 2 | 3070 | 0.000651 | `True` | 4 | 0.0156103 | 22945.426 |
| serial_lpc1 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 130 | 2942 | 0.042318 | `True` | 130 | 0.0065519 | 19304.684 |
| serial_lpc16 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 10 | 3062 | 0.003255 | `True` | 10 | 0.0842604 | 21180.516 |
| serial_lpc2 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 66 | 3006 | 0.021484 | `True` | 66 | 0.0075567 | 19585.58 |
| serial_lpc4 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 34 | 3038 | 0.011068 | `True` | 34 | 0.0109817 | 19954.522 |
| serial_lpc8 | single_r64_ranker | 50257 | 768 | 128 | 32768 | 64.0 | 3072 | 18 | 3054 | 0.005859 | `True` | 18 | 0.014957 | 20013.574 |

## Assumptions

- Producer rows are the existing stage-serialized output-projection service model.
- Ranker service is measured at r64/k1 and compared to producer tile arrival cadence.
- single_r64_ranker scans wider producer tiles sequentially through one r64 ranker.
- banked_r64_rankers assumes one measured r64 ranker instance per 64 producer lanes.
- throughput_ok means ranker service for one producer tile is no slower than producer_ii_cycles.
- This is a service-time compatibility model; it does not replace ready-valid RTL equivalence.
