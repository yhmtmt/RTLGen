# Design Brief

The prior exact activity job validates five isolated phases but cannot measure
simultaneous VC0/VC1 arbitration. The integrated GQA8 artifact records final
root bounds and counts, not cycle-aligned shared-SRAM residency or local
reducer release events, so one authoritative mixed release schedule is not
available.

This job keeps every exact phase flit and replays them on one registered-credit
deterministic-XY mesh. Endpoint injection is compared with a per-VC
round-robin arbiter and an arrival-ordered FIFO. The first VC1 group starts at
0, 25, 50, 75, or 100 percent of the measured VC0 service duration; later VC1
groups retain the sequential two-slot adapter lifecycle.

The isolated source traces continue producing while their shared queue is
blocked. Consequently the maximum queued flits are a required-buffer bound.
Only rows with at most one queued flit per VC are directly compatible with the
current one-register ready/valid source boundary.

The two-source arbiter is now embodied and cycle-equivalent. Physical cost and
integration into the currently separate VC0 and VC1 mesh owners remain open.
