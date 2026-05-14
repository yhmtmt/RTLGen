# Decoder Producer/Ranker Ready-Valid Equivalence

- model: `decoder_producer_ranker_ready_valid_equivalence_v1`
- target: `r64_k1_nm16_ready_valid_equivalence`
- decision: `ready_valid_equivalence_passed`
- next_step: Queue a bounded macro-style r64/k1 producer-to-ranker physical wrapper.

## Checks

| check | passed | observed |
|---|---|---|
| producer_lanes_match_r64_target | `True` | `64` |
| top_k_matches_first_target | `True` | `{'rank_top_k': 1, 'merge_top_k': 1}` |
| token_id_width_covers_gpt2_vocab | `True` | `16` |
| rtl_stream_matches_full_vocab_reference | `True` | `{'token': 5, 'logit': 500, 'accepted': 3, 'stalls': 0, 'fifo': 1, 'cycle': 7}` |

## RTL Simulation

- status: `ok`
- expected: `{'token': 5, 'logit': 500}`
- observed: `{'token': 5, 'logit': 500, 'accepted': 3, 'stalls': 0, 'fifo': 1, 'cycle': 7}`

## Assumptions

- The harness validates stream ordering, lower-token tie-break, final last-beat completion, and merge observables for the first r64/k1 target.
- The current wrapper is a functional ready-valid harness, not the final physical macro implementation.
- nm16 producer config is used as measured MAC-context metadata; the harness feeds deterministic logit tiles directly.
