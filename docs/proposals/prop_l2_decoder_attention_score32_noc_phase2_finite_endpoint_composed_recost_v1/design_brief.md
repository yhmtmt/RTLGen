# Design Brief

The recost validates endpoint equivalence against the canonical schedule,
selects `max(source NoC clock, composed critical path)`, and replays every
packet through the finite endpoint performance model. The merged equivalence
artifact establishes that this model matches RTL cycle and router counters.

The physical accounting subtracts the prior per-cluster router, FIFO, and
endpoint estimates from the source logic totals before adding the aggregate
composed footprint and vectorless power. SRAM area remains included, while its
dynamic access energy is excluded until workload-to-macro port activity exists.
