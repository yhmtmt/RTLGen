# prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1

This proposal extends the composed score32 GQA8 cluster-SRAM equivalence gate
from one logical head group to the full four-group `head_base=0,8,16,24`
rotation. The purpose is to prove that distinct command IDs, rotated p54/p53
extra-block ownership, bounded fill traffic, and finalized root rows remain
exact before the measured Llama7B model consumes this hierarchy as a full
attention score service.

Dispatch uses `control_plane/scripts/run_bounded_command.py`. When a usable user
`systemd` manager exists, the launcher applies the contract through
`systemd-run --user --scope`; otherwise it falls back to process-group timeout,
`RLIMIT_AS` / `RLIMIT_NPROC`, and a CPU-affinity ceiling derived from the
current allowed CPUs and the requested quota rounded to whole CPUs. Timeout,
OOM, or other resource termination remains inconclusive in either backend.

The remote job requests `--sim-backend fine_compositional_icarus`. The existing
strict generated-top guard first proves regeneration, module multiplicity,
boundary wiring, ordering, and semantic contracts. The probe serially replays
the exact single-producer RTL for every cluster/producer/command stimulus and
checks output rows plus SRAM request metadata. It then simulates the concrete
p54/p53 SRAM endpoint and local reducer/temporal-merge modules before driving
the observed cluster rows through the concrete global tree. No module
containing all 53 or 54 producers is elaborated; producer, SRAM, reducer,
temporal-merge, ordering, and finalizer behavior remain RTL.

The prior Icarus component compile phases succeeded, but concurrent p54 `vvp`
replays were operationally cancelled at about 3.45 GiB RSS each when aggregate
memory reached the 12 GiB container limit plus 2 GiB swap; this was not an RTL
mismatch. An isolated flat-Verilator p54 compile under 8 GiB `RLIMIT_AS` also
failed with return 255 and `std::bad_alloc` after 12.3 seconds, with no binary.
The probe also carries a distinct `--compile-timeout-sec 1200` while the
simulation timeout remains `--timeout-sec 3600`. The bounded launcher contract
is widened to a 5100-second outer timeout and a 1500-second stall timeout so a
quiet component compile is not misclassified as a failed simulation.
