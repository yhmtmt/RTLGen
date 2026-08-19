# Score32 Exact Stats-Once Transport Codec PPA

This proposal compares the exact stats-once group codec against the aligned
two-flit codec under one matched canonical source, sink, and stall harness.

The dense codec carries one eight-head aggregate group in 167 256-bit flits
instead of 256 flits while preserving every 41-bit value numerator and each
head's exact maximum and exponential sum.
