# Exact Stats-Once Shared-Root SRAM Bank Frontier

## Registered-SRAM Full-Chain RTL

| banks | 64x32 macros | root span cycles | final cycle | latency vs B15 | component throughput vs B15 |
|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 3901 | 4120 | +57.251908% | 0.635922 |
| 4 | 32 | 2939 | 3077 | +17.442748% | 0.851479 |
| 8 | 64 | 2733 | 2855 | +8.969466% | 0.917688 |
| 15 | 120 | 2505 | 2620 | +0.0% | 1.0 |

## Inferred-Memory Diagnostic Model

| banks | 64x32 macros | root span cycles | replay drain cycles | iterations |
|---:|---:|---:|---:|---:|
| 2 | 32 | 2628 | 64 | 24 |
| 4 | 32 | 2505 | 13 | 1 |
| 8 | 64 | 2505 | 8 | 1 |
| 15 | 120 | 2505 | 8 | 1 |

## Current Candidates

B4 minimizes SRAM count, B15 maximizes measured throughput, and B8 is intermediate; energy and placed control area are not yet measured.

- B4: `73.333333%` fewer macros than B15, `+17.442748%` latency
- B8: `46.666667%` fewer macros than B15, `+8.969466%` latency
- B15: measured full-chain throughput anchor
- B2 is dominated by B4 at the same 32-macro count
- arithmetic and precision are unchanged; storage and replay remain bit-exact

## Full-Chain RTL Validation

B2, B4, B8, and B15 pass the finite transport, registered SRAM, decoder, and exact global-tree composition:

- `1920` canonical remote beats, `2505` flits, and `315` packets
- `128` exact final rows with every output lane equal to `65535`
- structural tests retain the expected `32`, `32`, `64`, and `120` SRAM macros

## Limits

- Macro PPA and placed control timing await evaluator measurement.
- Cycle results use the available registered fakeram45 behavioral model; post-route clock frequency is not yet applied.
- The inferred-memory model remains diagnostic only and does not select the physical bank point.
- Precision is unchanged because packet storage and replay are bit-exact.
