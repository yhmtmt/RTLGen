# Exact Stats-Once Shared-Root SRAM Bank Frontier

| banks | 64x32 macros | root span cycles | replay drain cycles | iterations |
|---:|---:|---:|---:|---:|
| 2 | 32 | 2628 | 64 | 24 |
| 4 | 32 | 2505 | 13 | 1 |
| 8 | 64 | 2505 | 8 | 1 |
| 15 | 120 | 2505 | 8 | 1 |

## Selection

Four banks are selected: minimum 32-macro count while retaining the exact 2505-cycle root serialization floor.

- macro reduction versus 15 banks: `73.333333%`
- replay-drain increase versus 15 banks: `5` cycles
- two-bank transport-span penalty: `4.91018%`
- one bank is excluded because it uses the same 32 macros as four banks with fewer ports
- arithmetic and precision are unchanged; storage and replay remain bit-exact

## Full-Chain RTL Validation

The selected B4 point passes the finite transport, decoder, and exact global-tree composition:

- four retained `64x256` physical memories (`32` available `64x32` macros)
- `1920` canonical remote beats, `2505` flits, and `315` packets
- `128` exact final rows with every output lane equal to `65535`
- unchanged `2505`-cycle root delivery span
- final cycle `2613`, versus `2600` for fifteen banks (`+13`, `+0.5%`)

## Limits

- Macro count uses available 64x32 granularity; macro PPA awaits evaluator measurement.
- The model excludes decoder/tree backpressure; the selected B4 point has separate full-chain RTL timing evidence.
- Precision is unchanged because packet storage and replay are bit-exact.
