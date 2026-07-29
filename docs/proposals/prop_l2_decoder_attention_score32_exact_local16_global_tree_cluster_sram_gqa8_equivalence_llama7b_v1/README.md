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

The remote job now requests `--sim-backend verilator_hierarchical` so Verilator
can use `--binary --timing --hierarchical` with exact control-file markings for
the generated p54 cluster, p53 cluster, and global-tree modules. This keeps the
generated top RTL, testbench, memh sidecars, stdout contract, and structured
row oracle unchanged while avoiding Icarus monolithic elaboration blow-up.
The probe also carries a distinct `--compile-timeout-sec 1200` while the
simulation timeout remains `--timeout-sec 900`. The bounded launcher contract
is widened to a 2400-second outer timeout and a 1500-second stall timeout so a
quiet hierarchical compile is not misclassified as a failed simulation. Timeout,
OOM, or other resource termination remains inconclusive.

See `evaluation_gate.md` for the exact remote resource and acceptance contract.
