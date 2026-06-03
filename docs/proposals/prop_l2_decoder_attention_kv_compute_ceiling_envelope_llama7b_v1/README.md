# Llama7B Attention/KV Compute Ceiling Envelope

This proposal bounds the Llama7B 131k attention/KV frontier by physically
plausible compute-density ceilings.

The goal is to compare the current measured RTLGen compute density with
optimistic external-reference envelopes before assuming that detailed SRAM/NoC
or HBM-controller modeling is the dominant next problem.

