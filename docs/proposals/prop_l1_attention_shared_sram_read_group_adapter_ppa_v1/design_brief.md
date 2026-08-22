# Design Brief

The shared-SRAM macros expose 1024-bit words while the remote NoC path emits
256-bit beats and the local value-fill path emits 512-bit beats.  The adapter
collects four or two ordered beats into one macro write and replays a macro
read as the corresponding ordered output beats.  One-slot points establish the
minimum control cost; two-slot points test whether fill and drain can overlap.

The adapter owns only grouping, metadata, buffering, ready/valid behavior, and
malformed-transaction rejection.  Shared-SRAM capacity, macro timing and
energy, the 17-bank K scheduler, the NoC, and external DRAM remain separate
composition terms.
