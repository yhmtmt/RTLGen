# Evaluation Gate

Require RTL/performance-model agreement for addresses, complete payloads,
ordering, transaction counts, backpressure, and protocol rejection for all
four width/slot points.  Generated artifacts must pass the proposal-link and
manifest guard before OpenROAD.  Report routed timing, standard-cell area,
power, and failures separately for each point; do not mix macro area or access
energy into adapter metrics.

Use the checked 260-by-260 um core at placement density 0.50.  Reject any run
that removes the declared 1,024 payload bits per slot or reintroduces reset on
payload state.  The generated manifest must identify the kept full response
bus, minimal synthetic response source, and included narrow-I/O overhead.
