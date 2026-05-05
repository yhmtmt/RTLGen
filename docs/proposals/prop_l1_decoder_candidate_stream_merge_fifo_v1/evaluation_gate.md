# Evaluation Gate

Queue `l1_decoder_candidate_stream_merge_fifo_v1` only after the generator support for `candidate_stream_merge_fifo` is merged and materialized on the evaluator.

The local gate is:

- `cmake --build build --target rtlgen`
- `bash tests/test_candidate_stream_merge_fifo.sh`
- `ctest --test-dir build -R candidate_stream_merge_fifo --output-on-failure`
