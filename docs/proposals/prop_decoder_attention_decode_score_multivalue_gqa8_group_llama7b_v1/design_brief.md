# GQA8 Shared-K/V Multivalue Group

Llama7B has 32 query heads and four K/V heads. Each K/V head therefore serves
eight query heads. The previous frontier priced a complete 128-dimensional
query-head path but treated each head as an independent value consumer. This
candidate embodies one full GQA8 group:

1. Broadcast each shared key beat to eight distinct query-head score paths.
2. Compute the eight query-head score tensors in parallel.
3. Require the eight value replay addresses and slices to agree.
4. Issue one external 512-bit value request and broadcast its response.
5. Serialize 128 result beats in head-major, then slice-major order.

This changes transport and sharing, not the signed-int8/s32/LUT-softmax
arithmetic contract. The equivalence gate therefore composes eight real
single-cluster RTL arithmetic runs with a separate wrapper protocol simulation.
It records that no flat eight-cluster RTL equivalence simulation was run.

The group contains eight score-bank proxies, each with 56
`fakeram45_2048x39` macros, for 448 macros total. At 206.910 by 219.800 um per
macro, raw macro area is 20.374510 mm2. The square macro-only lower bound is
4.514 mm; at the existing 40% density assumption it is 7.137 mm before routing
and standard-cell margin. The physical sweep therefore starts at a 7.2 mm die
and adds 8.0 and 9.0 mm points instead of reusing the infeasible 2.5 to 3.0 mm
single-cluster envelope.
