# Exact shared-root storage macro PPA

This package prepares four remote Nangate45 physical-calibration items for the
registered shared-root packet SRAM frontier. It does not dispatch development
branch code.

Full-chain RTL with the available `fakeram45_64x32` behavioral model changes
the frontier materially. B2/B4/B8/B15 complete in 4120/3077/2855/2620 cycles
while preserving all 1920 canonical remote beats and all 128 exact final rows.
B2 is dominated by B4 at the same 32-macro inventory. B4, B8, and B15 remain
candidates until physical control area and power are measured.

The floorplans scale with raw macro inventory to keep macro utilization near a
common range: 400 um square cores for B2/B4, 550 um for B8, and 750 um for B15.
This avoids interpreting congestion from a fixed undersized core as a bank
architecture penalty.

Each accepted metrics row must retain `macro_count`, `macro_area_um2`,
`blackbox_instance_counts`, `missing_blackboxes`, and `macro_manifest_path`.
The bank comparison is invalid if the CSV cannot prove the expected 32, 32,
64, and 120 physical SRAM instances; a passing pre-synthesis guard alone is
not sufficient evidence for the placed result.

After all four metrics files merge, run
`npu/eval/audit_attention_score32_exact_shared_root_storage_physical_frontier.py`.
It verifies the macro inventory, applies each post-route critical path to the
exact full-chain cycle count, and reports separate latency, instance-area, and
vectorless-energy Pareto winners. The audit requires a measured system clock
floor and uses `max(storage critical path, system clock floor)`; storage PPA
alone cannot claim full-chain timing. It deliberately does not collapse those
dimensions into a scalar score or claim per-token energy before hierarchical
Llama7B schedule recosting.

At queue time, use merged `origin/master` as the source commit. Each normal L1
task-generation request must place that SHA in
`source_requirement.required_sha`.
