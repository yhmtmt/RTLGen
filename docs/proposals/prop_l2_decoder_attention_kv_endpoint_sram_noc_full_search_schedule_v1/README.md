# Endpoint SRAM/NoC Full-Search Schedule

This proposal checks whether practical SRAM-bank and endpoint service caps change
the selected Llama7B attention architecture point.

The previous endpoint SRAM/NoC constrained item applied caps only to retained
frontier rows from the topology-derived schedule. This item regenerates the full
endpoint-measured topology-derived schedule from the topology/scheduler pair
matrix, applies practical caps during ranking, and reports whether the best
topology/scheduler, die area, SRAM split, or service bottleneck moves.

