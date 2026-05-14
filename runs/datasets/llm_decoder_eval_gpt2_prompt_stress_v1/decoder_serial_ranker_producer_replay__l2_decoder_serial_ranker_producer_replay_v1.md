# Decoder Serial Ranker Producer Replay

- model: `decoder_serial_ranker_producer_replay_v1`
- decision: `producer_cadence_replay_passed`
- throughput_safe_rows: `6/12`
- next_step: Promote serial_lpc1 into a producer-coupled RTL wrapper if the chosen producer cadence matches the output-projection service model; keep lpc2/lpc4 as guard points for faster resident-weight producer assumptions.

## Replay Rows

| lpc | scenario | producer II | service | expected ok | rtl | token | logit | backpressure | final cycle |
|---:|---|---:|---:|---|---|---:|---:|---:|---:|
| 1 | ii16 | 16 | 65 | `False` | `ok` | 5 | 500 | 310 | 397 |
| 1 | ii33 | 33 | 65 | `False` | `ok` | 5 | 500 | 293 | 397 |
| 1 | ii65 | 65 | 65 | `True` | `ok` | 5 | 500 | 15 | 397 |
| 1 | ii384 | 384 | 65 | `True` | `ok` | 5 | 500 | 0 | 1987 |
| 2 | ii16 | 16 | 33 | `False` | `ok` | 5 | 500 | 150 | 205 |
| 2 | ii33 | 33 | 33 | `True` | `ok` | 5 | 500 | 15 | 205 |
| 2 | ii65 | 65 | 33 | `True` | `ok` | 5 | 500 | 0 | 360 |
| 2 | ii384 | 384 | 33 | `True` | `ok` | 5 | 500 | 0 | 1955 |
| 4 | ii16 | 16 | 17 | `False` | `ok` | 5 | 500 | 30 | 109 |
| 4 | ii33 | 33 | 17 | `True` | `ok` | 5 | 500 | 0 | 184 |
| 4 | ii65 | 65 | 17 | `True` | `ok` | 5 | 500 | 0 | 344 |
| 4 | ii384 | 384 | 17 | `True` | `ok` | 5 | 500 | 0 | 1939 |

## Assumptions

- The replay uses the same generated serial-ranker RTL wrappers measured in the architecture sweep.
- Producer tiles are released at fixed issue intervals; if the ranker is busy, the testbench holds valid and counts backpressure.
- The RTL output is checked against a full-token top-1 reference with deterministic lower-token tie-break.
- This validates stream behavior and cadence tolerance; it is not a new physical PPA measurement.
