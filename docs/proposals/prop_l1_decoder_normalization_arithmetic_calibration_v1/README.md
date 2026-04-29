# Decoder Normalization Arithmetic Calibration

This workspace tracks the first RTLGen-backed calibration step for the decoder
normalization cost proxy. The current proxy is a hand-written planning model.
It is useful for choosing what to measure next, but it is not a literature
model and it is not measured Nangate45 PPA.

The requested L1 work measures multiplier and adder primitives that bound the
q8 reciprocal-normalization path. Divider and bf16 reciprocal blocks are
explicit follow-ups because RTLGen does not currently expose standalone config
support for them.
