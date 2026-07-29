# Full score32 GQA8 cluster-SRAM equivalence

This proposal gates the first complete RTL path from 856 score32 producers
through sixteen concrete cluster SRAM services and local reducers into the
ordered finalized tree.

The job is an equivalence and service-observability gate, not a physical PPA
claim. A pass permits the measured cycle and traffic behavior to enter the
Llama7B architecture model. It does not close HBM timing, SRAM macro PPA, mesh
NoC behavior, or full-array physical feasibility.

See `evaluation_gate.md` for the exact remote resource and acceptance contract.
