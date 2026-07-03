# L1 decoder-attention command dispatch control PPA

This proposal adds a concrete central command-dispatch/control microblock for
the Llama7B attention schedule. It measures the command FIFO, round-robin
cluster selection, per-cluster in-flight accounting, ready/valid issue path,
and compact dispatch payload timing/area/power.

This does not replace the existing exp-LUT command-overhead sensitivity job.
Instead, it provides a measured control anchor that can later bound or replace
the per-tile/per-wave command-cycle assumptions used by that L2 recost.

The distributed control network, clock-domain crossings, and per-cluster local
decode are still remaining abstractions.
