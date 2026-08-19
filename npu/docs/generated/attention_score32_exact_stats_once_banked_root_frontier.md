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

## Limits

- Macro count uses available 64x32 granularity; macro PPA awaits evaluator measurement.
- The model includes single-port conflicts and slot-release feedback but not decoder/tree backpressure.
- Precision is unchanged because packet storage and replay are bit-exact.
