# Llama7B SRAM/NoC Constrained Schedule

This proposal queues the follow-on L2 scheduler run after the topology-derived
dense-tile frontier. The job consumes the merged topology-derived schedule and
the measured SRAM tile-buffer profile, then applies practical caps for:

- local tile-buffer capacity per cluster
- 256-bit SRAM-bank read service
- endpoint injection/ejection service per cluster
- topology-derived aggregate NoC payload service

The purpose is to correct the optimistic abstract SRAM-bank bandwidth in the
previous scheduler while keeping the NoC topology/scheduler coupling from the
valid topology-pair result.

Expected output:

- revised Llama7B dense-tile frontier under practical SRAM/NoC endpoint caps
- slowdown versus the topology-derived schedule
- cap-source counts showing whether topology, endpoint, or SRAM-bank service is
  limiting the retained frontier
- best rows by topology and endpoint/SRAM setting
