# Llama7B score32 exp-LUT divider measured command-control recost

This proposal adds a dependency-gated L2 recost that consumes the measured L1
attention command-dispatch/control PPA and charges it to the score32 exp-LUT
divider reduced-replica Llama7B schedule.

It is distinct from the command-overhead sensitivity job:

- command-overhead sensitivity sweeps assumed per-tile/per-wave cycles
- measured command-control recost charges measured central scheduler/control
  area, power, and clock

The result should run only after the exp-LUT quality/PPA/base-recost chain and
the L1 command-dispatch-control PPA item have materialized.
