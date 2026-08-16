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
container without a user bus it falls back to process-group timeout,
`RLIMIT_AS`, descendant-tree task monitoring, and a CPU-affinity ceiling
derived from the current allowed CPUs and the requested quota rounded to whole
CPUs. The fallback does not use per-UID `RLIMIT_NPROC`, because remapped users
also own unrelated editor and daemon processes. In both modes, timeout, OOM,
or other resource termination remains inconclusive.

The remote job requests `--sim-backend fine_compositional_icarus`. The probe
first runs the existing strict generated-top regeneration, wiring, ordering,
and semantic guard. It then serially replays the concrete single-producer RTL
for every cluster/producer/command stimulus while checking exact output rows
and SRAM request metadata. Separate concrete p54/p53 simulations check the
SRAM endpoint responses and the real local reducer/temporal merge. A final
concrete global-tree simulation consumes the 16 observed cluster row streams.
The strict guard proves that these are the exact module boundaries and buses
used by the generated wrappers. The existing structured-row, count, and
protocol oracle judges the combined result. No module containing all 53 or 54
producers is elaborated, and no abstract arithmetic replaces RTL.

The previous component run reached all Icarus compile phases, but three
concurrent p54 `vvp` replays used about 3.45 GiB RSS each and were operationally
cancelled as aggregate memory reached the 12 GiB container limit plus 2 GiB
swap; it did not report an RTL mismatch. Ordinary flat Verilator is also
excluded: an isolated p54 compile under the exact 8 GiB `RLIMIT_AS` returned
255 after 12.3 seconds with `std::bad_alloc` and produced no binary.
The probe also carries a distinct `--compile-timeout-sec 1200` while the
simulation timeout remains `--timeout-sec 900`. The bounded launcher contract
is widened to a 2400-second outer timeout and a 1500-second stall timeout so a
quiet component compile is not misclassified as a failed simulation. Timeout,
OOM, or other resource termination remains inconclusive.

See `evaluation_gate.md` for the exact remote resource and acceptance contract.
