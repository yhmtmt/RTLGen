# Design Brief

The encoder retains one 419-bit exact aggregate beat and emits two ordered
256-bit flits. The decoder checks phase, aggregate beat-last, and zero padding before
reconstructing the identical beat. Both interfaces propagate ready/valid
backpressure and sustain one flit per cycle without inter-beat bubbles after
initial fill.

The physical harness uses an internal 32-bit deterministic source and folded
32-bit observation boundary. Its counters and source/sink support logic are
included in measured PPA. Reducer arithmetic, endpoint descriptors, SRAM,
router/mesh, global reduction, and HBM/DRAM are excluded.
