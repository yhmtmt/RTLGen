# Llama7B Architecture Closure Matrix

- source JSON: `npu/docs/llama7b_architecture_closure.json`
- generated Markdown: `npu/docs/generated/llama7b_architecture_closure.md`
- as_of: `2026-09-05`

## Headline

- closure counts: `closed=0`, `routed_with_caveat=1`, `measured_component=6`, `rtl_unmeasured=1`, `abstract_external=1`, `open=3`
- provisional recommendation: `INT8 dense compute` + `score32 + exp-LUT`, `hierarchical c1/c2 service islands`, `dual producer/reducer clocks`
- provisional because: The accepted c1 multivalue-service route is exploratory only: it is timing-clean but still carries 142 max-cap violations with worst slack -17.81 fF.
- provisional because: Producer-service-reducer composition is only bounded by partial equivalence and cadence audits, not by a full end-to-end measured composed implementation.
- provisional because: NoC, SRAM, and scheduler evidence are still mixed between measured primitives and analytic composition, so the final Llama7B recost is not yet a fully embodied chip closure.
- provisional because: External DRAM controller and PHY remain an intentional abstract boundary, so full-system signoff is outside the current on-chip closure claim.

## Component Status

| Component | Status | Confidence | RTL | Equivalence | Routed PPA | Activity | Composition | Scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Precision | measured_component | medium | closed | measured_component | measured_component | measured_component | measured_component | measured_component |
| Dense Compute | measured_component | medium | closed | closed | measured_component | open | measured_component | measured_component |
| Norm | open | low | rtl_unmeasured | open | open | open | open | open |
| Score/Softmax | measured_component | medium | closed | measured_component | measured_component | measured_component | measured_component | measured_component |
| Multivalue Service | routed_with_caveat | medium | closed | closed | routed_with_caveat | measured_component | measured_component | rtl_unmeasured |
| Reducer | measured_component | medium | closed | closed | measured_component | open | measured_component | rtl_unmeasured |
| Producer-Service-Reducer Composition | rtl_unmeasured | low | closed | measured_component | open | open | measured_component | measured_component |
| NoC | open | medium | measured_component | open | measured_component | open | open | open |
| SRAM | measured_component | medium | measured_component | measured_component | measured_component | open | measured_component | measured_component |
| Scheduler/CDC | open | low | closed | open | measured_component | measured_component | rtl_unmeasured | open |
| External Memory Boundary | abstract_external | high | abstract_external | abstract_external | abstract_external | abstract_external | abstract_external | abstract_external |
| Full Llama7B Recost | measured_component | medium | open | open | measured_component | measured_component | measured_component | measured_component |

## Precision

- status: `measured_component`
- confidence: `medium`
- summary: The current quality-backed path is INT8 compute with score32 plus exp-LUT softmax. Exact-div and q16 reciprocal variants were measured and rejected on generation quality, so the precision recommendation is bounded but still not exhaustively closed across mixed-format recovery options.
- next gate: Add any future BF16/FP quantization branch only after it passes the same Llama7B generation-quality gate and can be recosted with measured wrapper metrics.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | Score32 exp-LUT, exact-div, reciprocal-LUT, and replacement softmax paths all exist as RTL-backed candidate branches. |
| `equivalence` | `measured_component` | Behavior is bounded by generation-quality and replacement checks against the software reference, but not by a single full-hierarchy hash-equivalence proof. |
| `routed_ppa` | `measured_component` | Precision-sensitive wrapper cost is backed by measured composed-wrapper and schedule-wrapper rows rather than pure heuristics. |
| `activity` | `measured_component` | The promoted score32 schedule-wrapper activity audit provides a measured active-duty correction for the selected precision path. |
| `composition` | `measured_component` | The score32 exp-LUT service closure and integrated frontier ranking consume the measured wrapper path as the current precision-safe branch. |
| `scale_validation` | `measured_component` | The Llama7B ranking has been recosted around the selected score32 branch, but future FP formats and recovery flows can still move the frontier. |

Caveats:
- The precision claim is quality-backed for score32 exp-LUT, not for future FP quantization or QAT-assisted recovery paths.
- Equivalence evidence is still mixed between RTL/reference functional comparison and composed wrapper recost rather than one full-system tensor-hash proof.

Evidence:
- `docs/proposals/prop_l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1/analysis_report.md` (proposal_analysis; `rtl`, `equivalence`, `composition`): Records the passing score32 exp-LUT generation-quality branch used as the current precision recommendation.
- `docs/proposals/prop_l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1/analysis_report.md` (proposal_analysis; `equivalence`, `scale_validation`): Shows that the q16 reciprocal-LUT branch fails the Llama7B quality gate and cannot be promoted.
- `docs/proposals/prop_l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1/analysis_report.md` (proposal_analysis; `equivalence`, `scale_validation`): Shows that exact-div shares the same quality failure mode as the reciprocal-LUT branch.
- `docs/proposals/prop_l2_decoder_attention_score32_schedule_wrapper_activity_integrated_frontier_ranking_llama7b_v1/analysis_report.md` (proposal_analysis; `activity`, `routed_ppa`, `composition`): Captures the promoted activity-aware ranking used in the current precision-safe Llama7B frontier.

## Dense Compute

- status: `measured_component`
- confidence: `medium`
- summary: Dense GEMM capacity is backed by measured tile PPA and by the measured-compute Llama7B closure, which already invalidated the earlier abstract MAC/cycle frontier. The primitive is measured, but density recovery above the current floor is still open engineering work.
- next gate: Measure denser exact dense tiles or structurally different compute fabrics before promoting a compute-bound architecture conclusion.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | The dense GEMM tile family and clustered schedule consumers are implemented in RTL. |
| `equivalence` | `closed` | Primitive-level compute behavior is already gated by the existing RTL/perf-sim contract checks used for the measured GEMM path. |
| `routed_ppa` | `measured_component` | Measured tile rows and stability sweeps exist for the dense compute primitive family. |
| `activity` | `open` | The dense compute primitive has measured power, but a dedicated activity-backed closure for the final clustered array is not yet the controlling frontier input. |
| `composition` | `measured_component` | The measured-compute closure already replaces the old abstract MAC/cycle point in the Llama7B recost. |
| `scale_validation` | `measured_component` | Measured-compute and clustered-schedule closures bound the current density, but denser exact tiles remain unexplored. |

Caveats:
- The current measured floor is useful to falsify unrealistic throughput points, but it does not yet prove the best achievable dense-tile density.
- A future denser primitive can still move the compute/memory balance.

Evidence:
- `docs/proposals/npu/prop_l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`, `scale_validation`): Anchors the measured dense tile endpoint data used by the clustered schedule model.
- `docs/proposals/prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/analysis_report.md` (proposal_analysis; `routed_ppa`, `composition`, `scale_validation`): Documents the measured dense GEMM v3 closure used to replace abstract compute density in the Llama7B model.
- `docs/proposals/prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1/analysis_report.md` (proposal_analysis; `equivalence`, `composition`, `scale_validation`): Shows that the abstract 524288 MAC/cycle frontier is physically implausible at the measured exact dense-tile density.

## Norm

- status: `open`
- confidence: `low`
- summary: Normalization remains the weakest embodied datapath block. There are proposal tracks for arithmetic calibration and reciprocal datapaths, but the current Llama7B frontier still carries this area/energy contribution as an incompletely measured term.
- next gate: Promote one norm datapath with RTL equivalence, routed PPA, and direct integration into the Llama7B recost.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `rtl_unmeasured` | Reciprocal and normalization datapath proposals exist, but they are not yet promoted as the measured norm block used by the frontier. |
| `equivalence` | `open` | No full promoted norm equivalence record closes the behavior against the final frontier contract. |
| `routed_ppa` | `open` | The frontier still lacks an accepted routed normalization primitive replacing the remaining cost heuristics. |
| `activity` | `open` | No promoted activity-backed norm measurement is feeding the Llama7B recost. |
| `composition` | `open` | The norm path is not yet composed into the selected architecture with the same strength as score, reducer, or service. |
| `scale_validation` | `open` | There is no scale sweep proving that the chosen normalization structure remains valid across the intended architecture range. |

Caveats:
- Current norm accounting is not yet on the same measurement footing as dense compute, service, or the selected score32 softmax branch.
- BF16 and fixed-point norm options are both still unresolved.

Evidence:
- `docs/proposals/prop_l1_decoder_normalization_arithmetic_calibration_v1/quality_gate.md` (proposal_gate; `rtl`): Shows that normalization calibration work exists, but is not yet promoted as a closed measured component.
- `docs/proposals/prop_l1_decoder_bf16_recip_norm_datapath_v1/quality_gate.md` (proposal_gate; `rtl`): Tracks the BF16 reciprocal norm path that remains future work rather than a merged closure result.
- `docs/proposals/prop_l1_decoder_q12_pwl_recip_norm_datapath_v1/quality_gate.md` (proposal_gate; `rtl`): Shows that a fixed-point reciprocal norm path was explored but not promoted into the final frontier.
- `docs/proposals/prop_l1_decoder_q8_recip_norm_datapath_v1/quality_gate.md` (proposal_gate; `rtl`): Provides a second unresolved norm proposal branch, reinforcing that this block remains open.

## Score/Softmax

- status: `measured_component`
- confidence: `medium`
- summary: The selected score path is the score32 exp-LUT branch. It is quality-backed, has measured composed-wrapper and schedule-wrapper anchors, and has already been recosted into the Llama7B frontier, but it is still not a full-signoff hierarchy closure.
- next gate: Extend the exact hierarchy proof across the full group rotation before treating the score hierarchy as fully closed.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | The promoted score32 exp-LUT dual-stream datapath exists in RTL and is the current selected branch. |
| `equivalence` | `measured_component` | The branch is bounded by functional replacement and generation-quality checks, not by a single monolithic full-hierarchy tensor-hash equivalence gate. |
| `routed_ppa` | `measured_component` | Measured composed-wrapper and schedule-wrapper rows replace the old heuristic cost for the selected score path. |
| `activity` | `measured_component` | Activity-aware recost exists for the selected score32 schedule-wrapper family. |
| `composition` | `measured_component` | The score32 path has service closure, SRAM-envelope closure, HBM-service closure, and integrated frontier ranking consumers. |
| `scale_validation` | `measured_component` | The score32 path has been replicated into the Llama7B ranking, but full hierarchy rotation and final system signoff are still pending. |

Caveats:
- The chosen score path is still bounded by wrapper-level measurements rather than by a single final routed hierarchy.
- The one-group exact hierarchy proof is not enough to treat the full score hierarchy as completely closed.

Evidence:
- `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`): Captures the promoted L1 score32 exp-LUT composed datapath row.
- `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1/analysis_report.md` (proposal_analysis; `routed_ppa`, `composition`, `scale_validation`): Records that the selected L2 row is backed by the measured dual-stream wrapper metrics.
- `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1/analysis_report.md` (proposal_analysis; `equivalence`, `composition`): Defines the promoted service-closure record for the selected score32 branch.
- `docs/proposals/prop_l2_decoder_attention_score32_schedule_wrapper_activity_integrated_frontier_ranking_llama7b_v1/analysis_report.md` (proposal_analysis; `activity`, `composition`, `scale_validation`): Provides the activity-aware integrated ranking for the selected score32 schedule-wrapper family.

## Multivalue Service

- status: `routed_with_caveat`
- confidence: `medium`
- summary: The c1 multivalue-service island now has accepted routed PPA, exact integrated-service composition, and promoted strict composed-service activity evidence. It remains exploratory routed component evidence rather than electrical signoff because the accepted row still carries max-cap violations, and the activity result measures only the direct service window instead of total-token energy.
- next gate: Keep the c1 electrical caveat explicit, then extend the same strict composed-service activity gate beyond c1 and fold the promoted anchor into the next service-aware Llama7B rerank.
- accepted c1 routed result:
  - tag: `decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1_macro_conservative_c1_die_3000`
  - critical path: `6.7148 ns`
  - die/core: `9.0 mm2` / `8.41 mm2`
  - instance/stdcell: `2.92145 mm2` / `0.295235 mm2`, `225327 cells`
  - utilization/vectorless power: `34.73781212841855%` / `0.26 mW`
  - route health: `DRC/setup/hold/slew clean`, but `142` max-cap violations, worst `-17.81 fF`

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | The multivalue service island exists as the exact integrated-service RTL path used by the current frontier work. |
| `equivalence` | `closed` | The c1 route is anchored to the merged exact integrated-service proof consumed by the Llama7B service model. |
| `routed_ppa` | `routed_with_caveat` | PR1548 accepted the c1 route as exploratory routed PPA: timing and route health are clean except for max-cap violations. |
| `activity` | `measured_component` | The strict c1 routed composed-service activity-power audit is promoted for the accepted route, with macro/sequential gates passing and only direct service-window component energy claimed. |
| `composition` | `measured_component` | The service family is now backed by exact integrated-service composition and a promoted c1 routed activity anchor instead of a free service placeholder. |
| `scale_validation` | `rtl_unmeasured` | Only the c1 island is accepted at this routed level; wider service-island scaling and electrical cleanup remain open. |

Caveats:
- Treat the c1 result as exploratory routed PPA only. It is not a signoff-clean macro.
- The accepted row is timing-feasible and route-clean for DRC/setup/hold/slew, but the remaining max-cap violations can still move buffer count, power, or timing once fixed.
- The promoted activity result measures direct c1 service-window component energy only. It is not a full-token or full-subsystem energy signoff.

Evidence:
- `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r3.json` (promotion_record; `equivalence`, `routed_ppa`): Promotion record for the accepted c1 routed row from merged PR1548.
- `runs/designs/npu_blocks/attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr/metrics.csv` (metrics_csv; `routed_ppa`): Contains the accepted c1 metrics row with 6.7148 ns critical path and 0.26 mW vectorless power.
- `runs/designs/npu_blocks/attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr/physical_signoff.json` (physical_signoff; `routed_ppa`): Canonical routed electrical review record: DRC/setup/hold/slew clean with 142 max-cap violations and worst slack -17.81 fF.
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_activity_power__l2_decoder_attention_decode_score_multivalue_service_c1_activity_power_llama7b_v1_r8.json` (activity_report; `activity`, `composition`): Promoted strict c1 composed-service activity-power evidence: macro and sequential activity gates pass, bank3 remains intentionally unforced, and only direct service-window component energy is claimed.
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_service_c1_activity_power_llama7b_v1_r8.json` (decision_record; `activity`, `composition`): Portable promotion/decision record for the accepted strict c1 composed-service activity result, preserving the routed_with_electrical_caveat qualifier and non-signoff scope.
- `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/analysis_report.md` (proposal_analysis; `rtl`, `composition`): Documents the exact integrated-service consumer that makes the c1 service island meaningful in the Llama7B model.

## Reducer

- status: `measured_component`
- confidence: `medium`
- summary: The reducer has moved well past heuristic cost: there are functional reducer branches, physical harness measurements, and Llama7B recost consumers. It is still a bounded component closure rather than a complete full-hierarchy proof across every cluster/wave combination.
- next gate: Promote the rotated full-group hierarchy proof before claiming the reducer is closed at the final clustered scale.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | Local temporal reducer and folded reducer branches exist in RTL. |
| `equivalence` | `closed` | Reducer functionality is already represented in the exact local-tree and local-reducer equivalence work. |
| `routed_ppa` | `measured_component` | Physical harness rows exist for the promoted score32 local temporal reducer family. |
| `activity` | `open` | There is no separate reducer-only promoted activity-power closure at the same level as the selected wrapper activity run. |
| `composition` | `measured_component` | The local reducer is already consumed in the score32 hierarchy and Llama7B local-reducer recost work. |
| `scale_validation` | `rtl_unmeasured` | The reducer is validated on bounded local structures, not yet on the full rotated hierarchy as a standalone scale closure. |

Caveats:
- The reducer is measured through promoted local and harness evidence, but not yet closed as a full-array standalone hierarchy proof.
- The final activity share is still mixed into larger composed wrappers.

Evidence:
- `docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/analysis_report.md` (proposal_analysis; `rtl`, `equivalence`): Documents the promoted score32 local temporal reducer branch and its physical-boundary diagnostics.
- `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r3.json` (promotion_record; `routed_ppa`): Promotion record for the accepted local temporal reducer physical harness row.
- `docs/proposals/prop_l2_decoder_attention_score32_local_reducer_measured_recost_llama7b_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Records the Llama7B consumer that recosts the measured local reducer into the architecture model.

## Producer-Service-Reducer Composition

- status: `rtl_unmeasured`
- confidence: `low`
- summary: The bounded exact hierarchy is now functionally composed across the producer, cluster-SRAM service, local reducer, and finalized global tree for the full four-group GQA8 rotation, and the corrected exact-reduction rerank already consumes that path. What remains open is a representative composed routed macro with measured activity, buffering/control overhead, and final system-level composition.
- next gate: Materialize a representative composed producer/service/reducer block with routed PPA and activity, then close the remaining CDC/buffering and memory-system composition gaps.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | Producer, service, and reducer sub-blocks all exist in RTL and have bounded composition wrappers. |
| `equivalence` | `measured_component` | One-group and four-group rotation equivalence gates now close the bounded full-GQA8 rotated hierarchy at functional level; the remaining gap is full-array physical/activity signoff rather than rotated-wave correctness. |
| `routed_ppa` | `open` | No accepted single routed macro composes producer, service, and reducer together at the selected clustered scale. |
| `activity` | `open` | The full producer-service-reducer activity pattern is still inferred from sub-block evidence and cadence audits. |
| `composition` | `measured_component` | The exact producer-to-cluster-SRAM-to-finalized-tree composition is closed by the four-group rotated hierarchy proof and is already consumed by the exact-reduction rerank, but no representative routed composed macro is accepted yet. |
| `scale_validation` | `measured_component` | The Llama7B exact-reduction rerank now replaces the obsolete one-group latency term with the four-group corrected hierarchy, while full-array routed PPA, toggle power, HBM fill, and NoC composition remain open. |

Caveats:
- Do not promote the bounded four-group RTL proof as representative composed-macro routed signoff.
- Producer-service-reducer throughput and energy still depend on open activity, CDC/buffering, HBM fill, and NoC composition closures.

Evidence:
- `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/analysis_report.md` (proposal_analysis; `rtl`, `equivalence`): Anchors the exact integrated service portion of the producer-service-reducer stack.
- `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1/analysis_report.md` (proposal_analysis; `equivalence`, `composition`): Historical one-group producer-to-SRAM-to-finalized-tree proof that the four-group rotated closure extends.
- `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1/analysis_report.md` (proposal_analysis; `equivalence`, `composition`): Promoted four-group rotation equivalence closes the bounded full-GQA8 rotated producer-to-SRAM-to-finalized-tree hierarchy.
- `npu/docs/generated/attention_score32_exact_partial_gqa8_dual_stream_producer_llama_wave_worst4_group_major.md` (generated_audit; `equivalence`, `composition`): Captures the worst-loaded producer cadence and command-distribution proof consumed by the bounded hierarchy analysis.
- `docs/proposals/prop_l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Shows the corrected exact-reduction rerank consuming the one-/four-group hierarchy evidence while keeping measured power, routed composed-macro, HBM fill, and NoC gaps explicit.

## NoC

- status: `open`
- confidence: `medium`
- summary: The repo has moved beyond a free NoC: the segmented 4x4 mesh now has promoted physical evidence, alongside endpoint-router anchors, traffic profiles, and exact shared-mesh arbitration/replay RTL. What is still missing is a promoted end-to-end equivalence gate and a frozen topology/scheduler pair for the final Llama7B claim.
- next gate: Measure the bare-router routed anchor, run exact hierarchy-matched post-route activity power, then fix the final topology/scheduler pair and rerun the clustered frontier.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `measured_component` | Endpoint-router primitives, the segmented 4x4 mesh, and exact shared-mesh arbitration/replay are represented in RTL-backed work. |
| `equivalence` | `open` | No single promoted equivalence gate closes the final selected NoC behavior against the end-to-end attention contract. |
| `routed_ppa` | `measured_component` | Endpoint-router anchors and the promoted segmented 4x4 mesh r7 physical result provide measured NoC component PPA. |
| `activity` | `open` | Exact traffic profiling exists, but hierarchy-matched post-route router activity power is still blocked on a promoted bare-router PPA anchor; traffic counts alone are not activity-backed energy. |
| `composition` | `open` | The final topology/scheduler composition at Llama7B scale is still under study rather than promoted as fixed. |
| `scale_validation` | `open` | Topology/scheduler pair studies exist, but a final selected pair is not yet closed as the architecture-level standard. |

Caveats:
- NoC costs are no longer free and a complete segmented-mesh physical anchor exists, but the final architecture still depends on a partially analytic topology/scheduler choice.
- The exact hierarchy-matched router activity job remains pending behind the bare-router routed anchor; current traffic profiling must not be labeled measured NoC energy.
- The current frontier can still move if the selected pair changes under stricter physical constraints.

Evidence:
- `docs/proposals/prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`): Provides a routed PPA anchor for one endpoint-router NoC primitive family.
- `docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`): Provides the promoted r7 physical anchor for the complete segmented 4x4 mesh; it is component evidence, not final topology closure.
- `docs/proposals/prop_l2_decoder_attention_noc_profile_v1/analysis_report.md` (proposal_analysis; `activity`): Captures traffic quantities used to remove the old free-NoC assumption, but does not provide VCD/SAIF-backed routed power.
- `docs/proposals/prop_l2_decoder_attention_kv_noc_scheduler_selected_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Documents a selected scheduler branch, but not yet a final physically closed architecture commitment.
- `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1/analysis_report.md` (proposal_analysis; `scale_validation`): Shows that topology/scheduler pairing work exists at Llama7B scale, but the pair space is not yet closed.

## SRAM

- status: `measured_component`
- confidence: `medium`
- summary: SRAM is on firmer ground than NoC: there are profile measurements, hierarchy-envelope studies, and bounded cluster-SRAM equivalence work. It is still a measured component, not a final memory-macro signoff across the full architecture.
- next gate: Measure workload-annotated SRAM macro/proxy activity, freeze SRAM with the final NoC/scheduler pair, and rerun the frontier under the chosen clustered hierarchy.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `measured_component` | Cluster-SRAM and local-SRAM structures are represented in the promoted attention hierarchy work. |
| `equivalence` | `measured_component` | Cluster-SRAM composition is bounded by the local16/global-tree GQA8 equivalence gate. |
| `routed_ppa` | `measured_component` | Promoted shared-SRAM read-adapter and k-round-scheduler rows now provide routed component evidence, while the final composed memory hierarchy remains unmeasured. |
| `activity` | `open` | SRAM access and CACTI profile evidence feeds the model, but workload-annotated activity on routed SRAM macro/proxy pins is not yet measured. |
| `composition` | `measured_component` | The score32 SRAM hierarchy envelope and cluster-SRAM equivalence gates are already consumed by the selected frontier. |
| `scale_validation` | `measured_component` | The SRAM hierarchy envelope indicates that conservative placement alone does not rerank the score32 frontier. |

Caveats:
- The SRAM model is materially better than a free-memory assumption, but it is still not a final top-level macro-floorplan closure.
- CACTI/access-profile energy must remain distinct from workload-annotated routed macro or proxy-pin activity power.
- The final clustered memory hierarchy can still change with the chosen NoC/scheduler pair.

Evidence:
- `docs/proposals/prop_l2_decoder_attention_sram_profile_v1/analysis_report.md` (proposal_analysis; `activity`): Provides the local SRAM access/profile evidence used by the attention model; it is not post-route activity-power evidence.
- `docs/proposals/prop_l1_attention_shared_sram_read_group_adapter_ppa_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`): Provides promoted PPA measurements for the shared-SRAM read-group adapter frontier.
- `docs/proposals/prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`): Provides promoted PPA measurements for the exact shared-SRAM K-round scheduler.
- `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1/analysis_report.md` (proposal_analysis; `rtl`, `equivalence`, `composition`): Anchors the bounded cluster-SRAM exact composition gate for the score32 hierarchy.
- `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Shows that the SRAM placement envelope does not materially rerank the selected score32 branch.

## Scheduler/CDC

- status: `open`
- confidence: `low`
- summary: Control and schedule overhead now has measured wrapper anchors, but the architecture still does not have a fully closed scheduler/CDC story for the final producer and reducer clock domains. This is the main reason the recommendation remains explicitly provisional.
- next gate: Promote one representative dual-clock composed scheduler path with explicit CDC buffering and consume it in the Llama7B frontier.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `closed` | Schedule-wrapper and command-control RTL exist for the promoted score32 branch. |
| `equivalence` | `open` | No promoted gate closes the final dual-clock scheduler and CDC behavior end to end. |
| `routed_ppa` | `measured_component` | Measured schedule-wrapper rows exist for bounded c2/c4 wrappers. |
| `activity` | `measured_component` | The schedule-wrapper activity ranking already adjusts the current score32 frontier. |
| `composition` | `rtl_unmeasured` | The dual producer/reducer clock plan is architecturally selected, but the final CDC/buffer composition is not yet promoted as one measured implementation. |
| `scale_validation` | `open` | The final scheduler remains sensitive to array hierarchy and memory service assumptions, so the larger-scale validity is still open. |

Caveats:
- The selected dual producer/reducer clock recommendation is architectural, not yet a complete promoted CDC closure.
- The scheduler result is still entangled with unresolved NoC and external-memory service assumptions.

Evidence:
- `docs/proposals/prop_l1_decoder_attention_dual_stream_schedule_wrapper_score32_exp_lut_v1/analysis_report.md` (proposal_analysis; `rtl`, `routed_ppa`): Provides the bounded schedule-wrapper PPA anchor for the selected score32 branch.
- `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_measured_command_control_llama7b_v1/analysis_report.md` (proposal_analysis; `routed_ppa`, `composition`): Documents the command-control recost consumed by the Llama7B score32 branch.
- `docs/proposals/prop_l2_decoder_attention_score32_schedule_wrapper_activity_integrated_frontier_ranking_llama7b_v1/analysis_report.md` (proposal_analysis; `activity`, `scale_validation`): Shows that measured schedule-wrapper activity already changes the integrated frontier numbers.
- `docs/proposals/prop_l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Captures the still-open on-chip service scheduling problem at Llama7B scale.

## External Memory Boundary

- status: `abstract_external`
- confidence: `high`
- summary: External DRAM controller and PHY are intentionally left abstract. This is not an untracked gap in on-chip work; it is the explicit project boundary for the current architecture-closure effort.
- next gate: No immediate on-chip gate. Keep using source-backed boundary sensitivity until the project scope expands to full-chip memory controllers.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `abstract_external` | Off-chip controller/PHY RTL is intentionally outside the current RTLGen closure scope. |
| `equivalence` | `abstract_external` | There is no off-chip controller equivalence claim because this boundary is intentionally abstract. |
| `routed_ppa` | `abstract_external` | No routed controller/PHY macro is required for the current on-chip closure claim. |
| `activity` | `abstract_external` | External memory energy/service terms are model-based boundary conditions, not embodied on-chip activity closures. |
| `composition` | `abstract_external` | The frontier consumes an external-service model at this boundary by design. |
| `scale_validation` | `abstract_external` | Boundary sensitivity is studied analytically rather than by controller/PHY implementation. |

Caveats:
- This boundary is intentionally abstract; it should not be counted as missing on-chip closure work.
- Any future full-chip tapeout study would need a separate controller/PHY program.

Evidence:
- `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1/analysis_report.md` (proposal_analysis; `rtl`, `equivalence`, `routed_ppa`, `activity`, `composition`, `scale_validation`): States that the remaining abstractions are cycle-accurate HBM controller RTL and vendor HBM current signoff.
- `docs/proposals/prop_l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_integrated_frontier_ranking_llama7b_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Shows that controller replay work exists as a boundary study rather than as a merged signoff controller implementation.

## Full Llama7B Recost

- status: `measured_component`
- confidence: `medium`
- summary: The full Llama7B frontier is no longer heuristic-only. It is recosted from measured compute, score/wrapper, service, SRAM, and activity anchors. The result is still a provisional architecture-level conclusion because several subsystem closures remain partial and external memory stays abstract.
- next gate: After the remaining on-chip component gates close, rerun the integrated ranking one more time and freeze the provisional best architecture as the project conclusion.

| Dimension | Status | Summary |
| --- | --- | --- |
| `rtl` | `open` | The full Llama7B architecture is still a recosted composition, not a single full-chip RTL/PnR closure. |
| `equivalence` | `open` | There is no whole-system tensor-hash equivalence proof for the full recosted architecture. |
| `routed_ppa` | `measured_component` | The recost consumes multiple measured routed or wrapper-level PPA anchors instead of using a free abstract core. |
| `activity` | `measured_component` | The score32 schedule-wrapper activity run is already folded into the integrated frontier. |
| `composition` | `measured_component` | Integrated ranking combines measured compute, selected score32 service closure, SRAM envelope, and HBM service models. |
| `scale_validation` | `measured_component` | The frontier has been reranked repeatedly under measured-component substitutions, but some key subsystem closures remain provisional. |

Caveats:
- This is an architecture-level recost, not a full-chip physical implementation.
- The result remains provisional until producer-service-reducer composition, scheduler/CDC, and the c1 service electrical caveat are tightened further.

Evidence:
- `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1/analysis_report.md` (proposal_analysis; `composition`, `scale_validation`): Records the conservative quality-backed HBM service frontier used as one baseline for the Llama7B recost.
- `docs/proposals/prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1/analysis_report.md` (proposal_analysis; `routed_ppa`, `composition`, `scale_validation`): Replaces the abstract compute density with measured dense-tile data in the Llama7B architecture ranking.
- `docs/proposals/prop_l2_decoder_attention_score32_schedule_wrapper_activity_integrated_frontier_ranking_llama7b_v1/analysis_report.md` (proposal_analysis; `activity`, `composition`, `scale_validation`): Provides the current activity-aware integrated ranking for the selected score32 branch.
- `docs/proposals/prop_l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1/analysis_report.md` (proposal_analysis; `routed_ppa`, `composition`, `scale_validation`): Summarizes the integrated score32 ranking that now replaces the older heuristic-heavy frontier.
