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
