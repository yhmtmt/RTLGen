# Design Brief

The source emits canonical 128-beat GQA8 groups. Each beat is 419 bits and the
maximum and exponential sum remain constant across the 16 slices of one head.
Both candidates consume the same sequence and use the same deterministic
backpressure and all-bit output fold.

The aligned candidate emits two 256-bit flits per beat, or 256 flits per group.
The stats-once candidate sends each head's 65 statistics bits once followed by
all sixteen 328-bit value vectors, or 42,504 bits and 167 flits per group. Its
encoder and decoder use bounded 768-bit reservoirs; neither stores a group.

The matched harness includes source, sink, counters, and both codec directions.
It excludes endpoint descriptors, SRAM, routers, local-reducer arithmetic, the
global reduction tree, and HBM/DRAM. The architecture uses 15 encoder/decoder
pairs, so measured pair PPA must be scaled by 15 before Llama7B recosting.
