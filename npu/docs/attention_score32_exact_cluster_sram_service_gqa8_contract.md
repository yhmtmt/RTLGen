# Score32 Exact Cluster SRAM Service GQA8 Contract

This block is the standalone per-cluster SRAM endpoint for the exact score32
GQA8 path. It is not a router and it does not claim SRAM macro closure.

## Scope

- exact `p53` and `p54` cluster variants only
- `2 x producers` value request and response lanes
- external HBM-return fill stream into local cluster SRAM
- `16` explicit independent banks selected by `value_slice`
- per bank storage: `buffer x stream x 64` rows of `512` bits
- capacity: `128 KiB` per buffer, `256 KiB` per cluster with double buffering

## Address And Mapping

- request addresses are relative to a producer-local allocation
- accepted requests require `address[13:3] == 0`
- accepted requests require `address[2:0] < producer_block_count`
- corrected p53 and p54 slot bases are fixed per head group
- each bank row index is `stream * 64 + resolved_block_slot`

## Arbitration And Backpressure

- each bank services at most one read per cycle
- arbitration is per-bank round-robin across producer-stream lanes
- requests to different banks may be accepted in the same cycle
- same-bank contention serializes and increments `bank_conflict_count`
- holding `valid` while `ready` is low is legal and does not itself raise a protocol error
- each lane has exactly one outstanding response slot; FIFO depth is `1`

## Fill And Residency

- a fill target selects `buffer`, `command_id`, `head_base`, and `wave`
- a complete fill writes `2048` unique rows into the selected buffer
- command accept requires an exact resident tuple match on that buffer
- duplicate writes to the same resident row are overwrite errors

## Counters

- counters advance by actual event multiplicity, not by per-cycle saturation
- simultaneous distinct-bank grants increment `request_accept_count` by the number of grants
- `bank_conflict_count` counts only extra contenders on the same bank
- response stall and accept counts track lane-by-lane handshake outcomes

## Caveat

The generated RTL uses inferred memories and resettable valid bits for contract
clarity. It is intentionally not macro-closed. Any physical replacement must
preserve the bank structure, ready/valid behavior, corrected slot mapping, and
counter semantics described here.
