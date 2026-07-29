# Full score32 GQA8 cluster-SRAM equivalence

This proposal gates the first complete RTL path from 856 score32 producers
through sixteen concrete cluster SRAM services and local reducers into the
ordered finalized tree.

The job is an equivalence and service-observability gate, not a physical PPA
claim. A pass permits the measured cycle and traffic behavior to enter the
Llama7B architecture model. It does not close HBM timing, SRAM macro PPA, mesh
NoC behavior, or full-array physical feasibility.

Dispatch uses `control_plane/scripts/run_bounded_command.py`. When the evaluator
has a usable user `systemd` manager the launcher applies the existing cgroup
limits through `systemd-run --user --scope`; when the evaluator is inside a
container without a user bus it falls back to process-group timeout, `RLIMIT_AS`
/ `RLIMIT_NPROC`, and a CPU-affinity ceiling derived from the current allowed
CPUs and the requested quota rounded to whole CPUs. In both modes, timeout,
OOM, or other resource termination remains inconclusive.

See `evaluation_gate.md` for the exact remote resource and acceptance contract.
