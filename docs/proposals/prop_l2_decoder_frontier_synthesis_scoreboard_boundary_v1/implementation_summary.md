# Implementation Summary

Adds an optional `--producer-control-boundary` input to the producer/ranker
coupling estimator. The Layer 2 frontier synthesis command now passes the
bounded SOFTMAX/EVENT guard artifact from
`l2_decoder_output_projection_producer_event_scoreboard_v1`.

The refreshed frontier report surfaces this boundary separately from producer
latency so the architecture decision does not confuse control-path feasibility
with output-projection service.
