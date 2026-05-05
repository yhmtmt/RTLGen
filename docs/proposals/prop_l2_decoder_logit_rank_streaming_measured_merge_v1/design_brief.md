# Design Brief

Use the existing streaming overlap sweep, but bind the candidate-stream merge/FIFO promotion artifact explicitly through the L2 task generator.

The report should answer three questions:

- whether measured merge/FIFO critical path changes the latency ranking versus flat measured rank
- whether area/power from local rank plus merge/FIFO makes the hierarchy unattractive even when overlap recovers cycles
- whether the equivalence contract remains visible in the artifact before any memory hierarchy or NoC work is added

This is still a rank-only decoder path. Temperature sampling, top-p, and probability reporting remain outside this job.
