# Evaluation Gate

Queue `l2_decoder_logit_rank_streaming_measured_merge_v1` only after:

- PR #405 has merged the candidate-stream merge/FIFO PPA artifact
- the L2 streaming model accepts `--candidate-merge-ppa`
- the L2 task generator records that artifact in its input manifest and command manifest

Acceptance:

- output JSON and Markdown include measured candidate merge/FIFO PPA
- component PPA fields include local ranker and candidate merge/FIFO terms
- perf-sim/RTL equivalence observables remain present
