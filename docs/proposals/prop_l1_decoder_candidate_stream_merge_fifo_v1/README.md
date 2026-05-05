# Decoder Candidate-Stream Merge FIFO

This proposal measures the first RTL block for the decoder logit-rank streaming hierarchy after the overlap model.

The block consumes local candidate groups through a ready-valid interface, buffers them in a bounded FIFO, merges candidates by logit with lower-token tie-break, and exposes the observables required for perf-sim/RTL equivalence:

- accepted candidate group count
- producer stall cycles
- FIFO max occupancy
- final completion cycle
- output valid mask, token ids, logits, and deterministic tie order

The first measurement targets top-1 and top-4, signed 16-bit logits, 16-bit token ids, and a 16-group FIFO.
