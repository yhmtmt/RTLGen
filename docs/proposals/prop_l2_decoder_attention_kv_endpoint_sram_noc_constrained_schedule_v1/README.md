# Endpoint SRAM/NoC Constrained Schedule

This proposal queues the endpoint follow-on to the topology-derived Llama7B
attention schedule. It consumes the endpoint-measured topology-derived schedule
from PR #805 and the measured SRAM tile-buffer profile, then applies practical
caps for:

- local tile-buffer capacity per cluster
- 256-bit SRAM-bank read service
- endpoint injection/ejection service per cluster
- topology-derived aggregate NoC payload service

HBM/DRAM service is intentionally inherited unchanged. The output should show
slowdown versus the endpoint topology-derived schedule and identify whether
topology service, endpoint service, or SRAM-bank service limits the retained
frontier rows.
