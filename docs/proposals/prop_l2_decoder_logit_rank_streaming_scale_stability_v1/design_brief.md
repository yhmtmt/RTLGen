# Design Brief

Extend the decoder logit-rank streaming overlap report from one GPT-2 vocabulary point to a small scale grid:

- vocabulary sizes: `50257`, `100000`, `200000`
- producer lanes: `8`, `16`, `32`, `64`, `128`
- local top-k: `1`, `4`
- producer II: `1`, `2`
- merge II: `1`, `2`
- FIFO depth groups: `16`, `256`, `4096`

The report must keep SRAM source data and NoC planning assumptions separate. The SRAM source is `runs/designs/sram/minimal_v0_2_draft/sram_metrics.json`; the NoC hop term remains a planning parameter.

Equivalence remains the same ready-valid stream contract: accepted `LogitTileStream` beats, accepted `CandidateStream` groups, producer stalls, FIFO occupancy, deterministic ordering, valid masks, and last-beat completion.
