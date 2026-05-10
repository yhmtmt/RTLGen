# Evaluation Gate

- Run `l2_decoder_producer_ranker_coupled_noc_v1`.
- Confirm producer II comes from output-projection compute and memory service.
- Confirm r64/r128/r256, top-k 1/4, and memory-share sensitivity rows are present.
- Confirm ranker FIFO validity and candidate traffic remain reported separately from producer service.
