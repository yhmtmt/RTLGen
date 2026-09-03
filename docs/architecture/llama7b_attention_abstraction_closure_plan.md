# Llama7B Attention Abstraction Closure Plan

## Goal

Quantify the remaining abstracted parts in the Llama7B 131k clustered attention
schedule until the selected frontier is backed by measured component costs rather
than free or heuristic assumptions.

## Current Measured Baseline

- Compute-array PPA is measured from the `compute_stability_cmp33` family.
- Local full-value attention tile PPA is measured by
  `l1_decoder_attention_full_value_tile_v1`.
- Tile-local SRAM profile evidence has been merged by
  `prop_l2_decoder_attention_sram_profile_v1` / PR #735.
- NoC traffic profile evidence has been merged by
  `prop_l2_decoder_attention_noc_profile_v1` / PR #736, using the measured
  FIFO/router primitive anchors from `l1_decoder_memory_noc_primitives_v1`.
- The integrated closure result
  `l2_decoder_attention_integrated_abstraction_closure_llama7b_v1` is merged by
  PR #963. It consumes the merged q12/PWL composed datapath feasibility result,
  the merged 7B quality-backed HBM frontier, and the native 7B KV-quality gate.
- The current selected Llama7B attention frontier is
  `physical_hbm_gqa8_kv8_service_frontier`:
  - latency: `30.944 us/token`
  - token throughput: `32316.442606 token/s`
  - die area point: `100.0 mm2`
  - precision: native-GQA `gqa8`, `kv8`
  - dominant resource: `hbm`
- The integrated energy-accounting closure
  `l2_decoder_attention_integrated_energy_closure_llama7b_v1_r2` is merged by
  PR #969. It reports:
  - total energy: `8.14357724928343 mJ/token`
  - energy status: `parameterized_integrated_energy_not_full_measurement`
  - dominant energy component: `hbm`
  - compute energy: `1.12424255488 mJ/token`, scaled from the nearest measured
    dense compute reference
  - HBM energy: `7.014935724818432 mJ/token`, using `8 pJ/byte`
  - NoC energy: `0.00427893972795392 mJ/token`, using byte-hop accounting
  - SRAM energy: `0.00012002985704362652 mJ/token`, scaled from CACTI macro
    profile evidence
- The HBM energy sensitivity result
  `l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1` is merged by
  PR #973. It reports:
  - latency/throughput best remains the `100.0 mm2` `gqa8/kv8` point at
    `30.944 us/token` and `32316.442606 token/s`
  - at the nominal `8 pJ/byte` HBM setting, energy best moves to the
    `400.0 mm2` `gqa8/kv8` point at `66.432 us/token`, `15052.986513 token/s`,
    and `4.719907157640776 mJ/token`
  - the frontier is therefore sensitive to the dominant HBM energy term and
    still needs HBM/DRAM service-energy closure before claiming an
    energy-optimal point
- The HBM/DRAM service-energy result
  `l2_decoder_attention_hbm_dram_service_energy_llama7b_v1` is merged by
  PR #975. It reports:
  - selected energy/latency/balanced family remains the `400.0 mm2` `gqa8/kv8`
    point with `tile_tokens=1024`
  - latency: `105.37783453568113 us/token`
  - token throughput: `9489.661695993555 token/s`
  - total energy: `3.8321431139716426 mJ/token`
  - compute energy: `2.41357553664 mJ/token`
  - HBM energy: `1.4021664896700032 mJ/token`, using explicit but unsourced
    command-class pJ parameters
  - dominant energy component under those parameters: `compute`
  - next result: calibrate HBM energy against source-backed aggregate HBM
    pJ/bit references before accepting the compute-dominance conclusion
- The source-backed HBM energy calibration result
  `l2_decoder_attention_hbm_energy_calibration_llama7b_v1` is merged by
  PR #977. It reports:
  - selected energy family remains the `400.0 mm2` `gqa8/kv8`
    `tile_tokens=1024` point
  - latency: `105.37783453568113 us/token`
  - token throughput: `9489.661695993555 token/s`
  - total energy with the HBM2 `3.97 pJ/bit` anchor:
    `11.522041553338012 mJ/token`
  - HBM energy: `9.092064929036372 mJ/token`
  - compute energy: `2.41357553664 mJ/token`
  - dominant energy component changes from `compute` under unsourced
    command-class pJ values to `hbm` under source-backed aggregate energy
  - next result: scale the command-class HBM service model to the source-backed
    HBM energy anchor and sweep row-hit sensitivity before claiming the final
    HBM energy ranking
- The HBM command-calibrated service result
  `l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1` is merged by
  PR #979. It reports:
  - selected energy family remains the `400.0 mm2` `gqa8/kv8`
    `tile_tokens=1024` point when retaining the abstract `524288 MAC/cycle`
    selected compute target
  - command-class energy scale to the HBM2 source anchor: `6.484297689339423`
  - row-hit sweep from `0.5` to `0.95` does not move the selected family
  - nominal row-hit `0.9` latency: `105.37783453568113 us/token`
  - nominal row-hit `0.9` energy: `11.522041553338012 mJ/token`
  - dominant energy component: `hbm`
  - next result: replace the abstract `524288 MAC/cycle` target with measured
    dense-tile compute capacity and recompute throughput/energy/area
- The measured compute energy closure result
  `l2_decoder_attention_measured_compute_energy_closure_llama7b_v1` is merged
  by PR #981. It reports:
  - the abstract `400.0 mm2` / `524288 MAC/cycle` frontier is not physically
    plausible at measured exact-FP16 dense-tile density
  - the abstract selected point would require `4096` copies of the best
    measured 128-MAC/cycle dense tile, or `1888.64512 mm2` of compute area
    before SRAM, HBM, NoC, and reserved area
  - the corrected measured-compute-constrained energy best is
    `die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512`
  - corrected latency: `72544.06213406654 us/token`
  - corrected token throughput: `13.784725731954872 token/s`
  - corrected energy: `81.66413005453946 mJ/token`
  - compute energy: `18.095420734855 mJ/token`
  - HBM energy: `63.520046663430314 mJ/token`
  - dominant energy component remains `hbm`, but throughput and area are now
    dominated by measured compute density
  - next result: measure denser exact-FP16 dense GEMM tiles before accepting the
    measured-compute frontier as the best possible exact-FP16 architecture
- The score32/w16 softmax quality branch is now the active precision-closure
  frontier:
  - the `score32_float` mixed-int8 generation-quality baseline passed with
    teacher-forced mean NLL delta about `0.0023`, top-1 match about `0.96875`,
    free-run exact match `0.75`, and free-run token match `0.84375`
  - the q16 reciprocal-LUT RTL softmax candidate
    `l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1`
    is merged by PR #1053 and failed the same quality gate:
    teacher-forced mean NLL delta `1.5337108926816854`, top-1 match
    `0.515625`, free-run exact match `0.0`, and free-run token match
    `0.078125`
  - the exact-divide RTL diagnostic item
    `l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1`
    is merged and also failed the generation-quality gate with the same
    teacher-forced mean NLL delta `1.533711`, free-run exact match `0.0`, and
    free-run token match `0.078125`. This indicates the reciprocal-LUT was not
    the dominant quality loss; the shared RTL softmax exponent/weight path is
    the problem.
  - the softmax-replacement quality item
    `l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1`
    is merged and restored the replacement branch enough to continue physical
    cost exploration.
  - measured composed-PPA reduced-replica recosts exist for score32 exact-div
    and score32 q16 reciprocal-LUT. Exact-div is area-fit only at a near-full
    compute budget (`801` required replicas, density gain `0.998929`), while
    the q16 reciprocal-LUT recost has more logic slack but is not
    quality-backed because its generation-quality gate failed.
  - the active score32 exp-LUT divider path has now materialized through
    quality, L1 composed-wrapper PPA, reduced-replica recost, command-overhead
    sensitivity, L1 command-dispatch-control PPA, and measured command-control
    recost. The measured command-control result is merged by PR #1194 and still
    reports `dual_stream_feasible`.
  - the wrapper-promotion audit
    `l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1`
    is merged by PR #1197. It records `l1_wrapper_metrics_match=True` and
    `requires_partitioned_or_cluster_validation=False`, so the reduced-replica
    score32 exp-LUT row can be treated as backed by the measured dual-stream
    wrapper metrics.
  - the service-closure audit
    `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1` is
    merged by PR #1199. It records `score32_supported=True`,
    `wrapper_metrics_match=True`, `latency_us=12519.342352`, and remaining
    abstractions `tile_local_and_shared_sram` plus `hbm_dram_service`.
  - the SRAM hierarchy envelope audit
    `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`
    is merged by PR #1201. It records `score32_exp_lut_sram_hierarchy_envelope_stable`;
    the conservative placement envelope changes HBM byte share by only
    `0.008045196` and projects `12621.763263 us`, so the score32 frontier is
    not materially reranked by SRAM placement efficiency alone.
  - the score32 HBM/DRAM service closure
    `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`
    is merged by PR #1203. It records
    `score32_exp_lut_hbm_dram_service_closure_hbm_sensitive`, best latency
    `12532.357427 us/token`, throughput `79.793447149 token/s`, HBM energy
    `134.280615241 mJ/token`, compute energy `360.550392645 mJ/token`, and
    total energy `494.831007886 mJ/token`. Remaining abstractions are
    cycle-accurate HBM controller RTL and vendor HBM current signoff.
  - the integrated score32 frontier ranking
    `l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1` is
    merged by PR #1205. It records score32 as the current precision-safe
    throughput frontier at `79.793447149 token/s`, `12532.357427 us/token`,
    `494.831007886 mJ/token`, and `800.0 mm2`. The measured exact-FP16 row
    remains the promotable energy reference at `81.66413005453946 mJ/token`.
    Score32 is `5.788540788x` faster but `6.059343405x` higher energy than
    that reference.
  - the reduced-parallel composed-wrapper PPA and recost are merged by
    PR #1212 and PR #1213. The L2 recost records that the selected measured
    local wrapper is
    `attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20`,
    with `856` area-fit replicas, `109568 MAC/cycle`, and
    `12322.504989 us/token` after measured wrapper clock/replica recost.
    The score32 compute-activity audit is merged and records active duty
    `0.957495485`, best clock-gated total energy
    `479.505988187 mJ/token`, and
    `5.871684274x` higher energy than the measured exact-FP16 reference.
  - the current immediate follow-on is
    `l1_decoder_attention_dual_stream_schedule_wrapper_score32_exp_lut_ppa_v1`.
    This measures a bounded c2/c4 RTL wrapper that composes central command
    dispatch, local issue/done accounting, and the selected score32 exp-LUT
    8x8 ppc1 dual-stream datapath. The purpose is to replace the modeled sum
    of command control plus local datapath with measured schedule-wrapper PPA
    before the full Llama7B array is recosted.
  - the prepared dependent recost is
    `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`.
    It must wait for the schedule-wrapper L1 PR to merge, then consume the
    c2/c4 metrics as measured compute/control blocks with manifest-derived
    wrapper MAC counts.
  - the composed score32 GQA8 cluster-SRAM equivalence gate for one logical
    head group is merged and bounded by
    `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1`.
    That gate proves the producer-to-SRAM-to-finalized-tree path only for
    `head_base=0` and eight waves.
  - the next bounded abstraction-closure gate is
    `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1`.
    It extends the same composed proof to the four-group `head_base=0,8,16,24`
    rotation with 32 total waves, distinct command IDs, rotated p54/p53
    extra-block ownership, 8192 cluster rows, and 512 root rows. The Llama7B
    score32 hierarchy should not be recosted from the one-group proof alone.
- New evaluations should continue to dispatch only to the remote evaluator
  `eval-daemon-b7c2d9c80c1c`, not the devcontainer.

## Active Closure Tranche (2026-08-11)

The historical ordering below records how the score32 frontier was reached, but
it is not the current queue. The active work is now limited to the following
evidence gaps:

- Exact-partial service correspondence: the immutable workload-correspondence
  retry and CDC lane-probe retry are queued. Their outputs are required before
  replacing the current service estimate with corrected exact-partial
  workload and lane evidence.
- RMSNorm: Phase 3 now has a reusable full-row BF16 RTL/performance-model
  equivalence gate, including ready/valid backpressure and protocol-error
  replay. The bounded physical wrapper job remains queued; its register-array
  storage must not be described as SRAM-macro evidence.
- NoC: the concrete five-port, 256-bit, four-VC segmented-router primitive PPA
  job is queued as `l1_segmented_xy_mesh_noc_phase1_v1`. Its first attempt
  failed before synthesis on evaluator runtime ownership. Before retry, the
  physical harness was also corrected from a zero-extending 32-bit data seed
  to full-width evolving 256-bit ingress state; results from the old harness
  would not qualify as physical evidence because synthesis could erase the
  upper 224 data bits. The complete 8-wave,
  128-tile schedule retry is queued as
  `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1`.
- Endpoint: `noc_sram_packet_endpoint` now embodies the Phase 2 logical
  zero-copy descriptor queues, source SRAM read handshake, 256-bit
  packetization, stable router injection, interleavable receive contexts,
  direct destination SRAM writes, completion backpressure, and protocol
  checks. Its packet metadata is compared exactly with the segmented-mesh
  performance model. The prepared L1 item
  `l1_noc_sram_packet_endpoint_phase2_v1` must measure endpoint PPA/service
  before the Phase 2 reroute can remove the endpoint-control cost abstraction.
- Composition: `noc_sram_packet_mesh4x4` connects sixteen finite endpoints to
  all sixteen routers with explicit scheduler descriptors, source SRAM reads,
  destination SRAM writes, completion, and protocol-error boundaries. The
  composed test proves simultaneous multihop packets and exact data/address
  delivery. Endpoint receive logic now rejects a flit whose destination does
  not name the local endpoint.
- Command scheduling: `noc_descriptor_pair_scheduler` now embodies the
  previously testbench-only packet issuer as a one-active-command controller.
  It gates on the concrete release cycle, holds RX and TX descriptors under
  endpoint backpressure, enforces an RX handshake on an earlier edge than TX,
  and accepts a replacement command when TX completes. The matching
  `serial_paired` performance policy is exact against composed RTL on the
  focused contention case and the complete 11,576-packet/92,128-flit replay.
  Full drain is 397,227 cycles, only 24 cycles above the merged parallel-issuer
  baseline, while contention/input stalls/peak occupancy fall from
  30,285/46,504/11 to 8,736/11,816/7. The prepared L1 PPA item and remote L2
  reproduction are required before removing scheduler cost and cadence from
  the abstraction list. Its command record is 102 bits. Sequential address
  generation, one outstanding read, one-cycle response capture, and a
  one-entry prefetch buffer are concrete RTL. Command SRAM bitcells, placement,
  macro energy, and the command population/inter-wave refill producer remain
  separate evidence rather than hidden flops.
- Physical composition: `l1_noc_sram_packet_mesh4x4_composed_ppa_v1` is
  retired. Its fixed 3.2 mm square floorplan was not derived from a successful
  aggregate route, and endpoint r4 still lacks the setup-path identity required
  by its own promotion gate. Create a replacement composed sweep only after
  aggregate r4 supplies a clean routed perimeter/floorplan and the endpoint
  path class is proven. The replacement must retain all endpoints, routers,
  links, scheduler descriptors, finite SRAM interfaces, completion
  backpressure, and all 256 payload bits; it is still not SRAM-macro evidence.
- Composed schedule substitution: the prepared
  `l2_decoder_attention_score32_noc_phase2_composed_mesh_reroute_llama7b_v1`
  item and its measured-router ancestors are retracted. They consumed the old
  16-bit/per-wave transport schedule, so their latency, traffic, and energy
  cannot be revised by scalar substitution. A replacement must consume the
  exact five-phase transport revision and a newly promoted endpoint/mesh
  composition, then keep SRAM macros plus workload-matched activity explicit.
- Credit timing: the original router FIFO allowed a full queue's input ready
  to depend on a same-cycle downstream pop. Across bidirectional links this
  formed a combinational ready fixpoint. FIFO credits now depend only on
  registered occupancy, and the performance model uses the same one-cycle
  full-queue recovery rule. Router, aggregate-mesh, and endpoint PPA items must
  use a merge commit containing this correction; the earlier queued source
  hashes are not valid final physical anchors.
- The original NoC Phase 2 item is superseded without a usable result. It
  interpreted compute-wrapper cycles as NoC cycles. The retry converts every
  release timestamp with
  `ceil(compute_cycles * compute_clock_ns / noc_clock_ns)` and records both
  clocks explicitly.
- The single-router PPA row may provide a measured router clock and a component
  area/power anchor. Summing router instances is only a component lower bound;
  it is not a placed 4x4 mesh result. Aggregate links, wiring, congestion,
  endpoint SRAM placement, and clock distribution remain explicit until an
  aggregate physical slice is measured.
- The exact transport revision supersedes the old per-wave schedule. It emits
  one VC0 phase with 7,616 packets / 60,928 flits and four VC1 phases with 315
  packets / 2,505 flits each, for 70,948 flits total. Packets use 419-bit link
  beats carrying a 328-bit payload under the actual-valid-ready, group-major
  contract. Any activity, composed-mesh, or frontier descendant must name this
  exact revision boundary; parameter-only recost of a retracted descendant is
  invalid.
- The VC0 portion of that revision is exact only for the historical
  fractional-smear traffic record, not for K/V tensor identity. Its aggregate
  2,228,224 resident bytes per layer equal the 68 MiB shared-SRAM capacity
  divided across 32 layers, but each context lacks K/V kind, head, tile,
  token, dimension, and partial-byte metadata. It therefore remains a
  resident-capacity transport bound and must not be connected directly to the
  cluster fill interface or used for a frontier recost. The canonical exact
  layer stream is 128 MiB: 64 MiB K and 64 MiB V. Locality-aware placement can
  eliminate remote transport only for resident-cache hits; it does not remove
  transient HBM-return traffic.
  Under the retained planar K/V layout, each layer's capacity allocation is
  two complete contiguous 1 MiB tiles plus a 128-token tail. The tail is not a
  contiguous 128 KiB range: it requires eight strided 16 KiB gathers, one per
  K/V head plane. The exact ingress scheduler must emit those descriptors.
- HBM/DRAM controller RTL and vendor current signoff remain outside the RTLGen
  chip boundary. They stay as source-backed service and energy envelopes, not
  as free components and not as claims of RTL closure.

### Promotion Standard

The final report must classify every candidate by evidence level instead of
mixing all rows in one ranking:

1. `functional_rtl`: every on-chip arithmetic, storage-control, scheduler, and
   communication slice used by the candidate exists as RTL and passes focused
   protocol/arithmetic tests.
2. `workload_equivalent`: composed RTL and the performance model agree on the
   complete declared workload, including outputs, ordering, traffic counts,
   release/completion cycles, and error behavior.
3. `physically_anchored`: each repeated primitive has measured PPA at an
   applicable clock/utilization point. Unmeasured aggregate wiring and
   placement terms are stated as bounds.
4. `composition_bounded`: the full Llama7B schedule uses only compatible
   measured rows or disclosed conservative envelopes. It must not infer
   full-array signoff from a primitive measurement.
5. `precision_backed`: the arithmetic/quantization profile has the applicable
   Llama7B quality result and is not promoted from a diagnostic proxy.

The project may conclude a **confidence-bounded best architecture** when one
candidate satisfies all five levels and remains best over the disclosed NoC,
SRAM-placement, and HBM/DRAM envelopes. Full monolithic RTL PPA is not required
when it is computationally infeasible, but representative composed slices and
utilization-matched physical anchors are required. A candidate that lacks any
level remains a planning frontier, not the final best architecture.

## Remaining Quantities

1. Full integrated energy closure
   - Scope: compose measured compute, local SRAM, NoC/router/FIFO, HBM service,
     q12/PWL datapath, and precision choices into one Llama7B energy metric.
   - Status: partially closed by PR #969. Token throughput, area, precision, and
     a measured-plus-parameterized energy account are now present, but the energy
     account explicitly reports
     `energy_status=parameterized_integrated_energy_not_full_measurement`.
   - Next result: remove or bound the dominant HBM pJ/byte sensitivity and the
     scaled compute-energy term before claiming an energy-optimal point.

1a. Measured compute capacity and energy closure
   - Scope: replace abstract selected-point `macs_per_cycle` and nearest-row
     compute-energy scaling with measured dense-tile replicated capacity rows.
   - Status: closed for the current measured dense-tile set by PR #981. The
     current exact-FP16 measured-compute frontier reaches about `132k
     MAC/cycle` only at the `1200.0 mm2` planning point, and the abstract
     `524288 MAC/cycle` selected point is infeasible.
   - Next result: run `l1_npu_dense_gemm_tile_scaling_v3` to measure whether
     16x16 exact-FP16 `k_unroll` depth scaling improves MAC/cycle/mm2 enough to
     rerank the Llama7B frontier.

2. HBM/DRAM and on-chip service detail
   - Scope: replace aggregate HBM efficiency and compact NoC/SRAM service caps
     with a more explicit controller, arbitration, and contention model.
   - Status: partially bounded by the HBM energy sensitivity result, the merged
     HBM/DRAM command-service energy result, and the source-backed aggregate HBM
     energy calibration result, plus the command-calibrated service result, but
     not cycle-accurate. The command-calibrated result preserved the selected
     energy family under row-hit sensitivity, but still reports analytic
     row-hit service, globally scaled HBM command energy, profile-scaled
     NoC/SRAM energy, and scaled compute energy.
   - Next result: keep HBM/DRAM as a bounded planning model for now, and move
     the immediate frontier work to quality-backed exp-LUT physical recost and
     explicit scheduler/control overhead accounting. A later HBM/controller job
     should replace the row-hit analytic model with a cycle service model only
     after the compute/softmax frontier is quality-backed.

3. Composed q12/PWL softmax datapath density recovery
   - Scope: score max, exponent approximation, sum accumulation, reciprocal
     normalization, normalized weight output, and value mixing inside the
     composed dual-stream attention wrapper.
   - Status: measured and consumed. The L2 consumer
     `l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1`
     reports `dual_stream_area_blocked`; the measured q12/PWL wrapper is
     available but the dual-stream frontier cannot be promoted on area/clock.
   - Next result: measure a denser fused attention datapath or reduce compute
     replicas before retrying dual-stream promotion.

4. Native 7B precision quality and KV4 recovery
   - Scope: teacher-forced decode on a real 7B-class checkpoint with KV8/KV4
     cache quantization feedback.
   - Status: 7B native quality evidence is merged. KV8 is conservative; KV4 is
     promising but below the cosine/KL caution line.
   - Next result: schedule QAT, scale-granularity recovery, or a larger 7B-class
     confirmation before treating KV4 as a precision-safe frontier point.

4a. Score32/w16 softmax quality closure
   - Scope: close the quality gap between the passing `score32_float`
     mixed-int8 baseline and an RTL-realizable score32/w16 softmax path.
   - Status: q16 reciprocal-LUT RTL softmax failed the bounded Llama7B
     generation-quality gate, and the RTL exact-divide diagnostic failed with
     the same quality signature. The reciprocal precision branch should not be
     promoted. The replacement branch is now the active path; the score32
     exp-LUT divider datapath and matching generation-quality gate are queued.
   - Next result: run the queued exp-LUT quality gate and exp-LUT L1 PPA on the
     remote evaluator, then release the blocked exp-LUT reduced-replica L2
     recost only if the release gate confirms both the passing quality result
     and the matching measured PPA row.

5. SRAM timing and energy
   - Scope: tile-local score/value buffering, KV tile reads, partial-value
     buffering, and result writeback.
   - Status: measured/merged by `l2_decoder_attention_sram_profile_v1`.
   - Remaining work: verify the final integrated schedule consumes the merged
     SRAM profile and reports any surviving SRAM abstraction as an explicit
     sensitivity term, not as an implicit ideal buffer.

6. NoC arbitration and contention
   - Scope: per-cluster local router/fifo cost is already measured, but current
     schedule still uses bandwidth divided by hop count for contention.
   - Status: measured/merged by `l2_decoder_attention_noc_profile_v1`.
   - Remaining work: verify the final integrated schedule consumes explicit
     payload/cycle and arbitration-latency bounds under the selected
   producer/reducer traffic mix.
   - Current refinement: router-plus-harness r7 and registered-boundary packet
     endpoint r4 are the active physical anchors. The exact node-5 RTL replay
     now shares a logic-free specialization top with
     `prop_l1_segmented_xy_router_node5_bare_ppa_v1`; this bare target is the
     prerequisite for hierarchy-matched post-route router energy. Its direct
     block sweep must use a parameter-hash-isolated OpenROAD flow variant for
     every physical point. The dependent
     `prop_l2_decoder_attention_score32_noc_router_postroute_activity_power_llama7b_v1`
     regenerates the full replay and measures every timing-feasible isolated
     route. Aggregate mesh placement remains required for links, congestion,
     and clock-tree power.

6a. Command/scheduler/control overhead
   - Scope: account for command generation, tile assignment, per-wave launch,
     ready/valid backpressure, and control distribution in the Llama7B
     composed-attention schedule.
   - Status: prepared by PR #1119. The new blocked item
     `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1`
     sweeps `command_cycles_per_tile=0,1,4,16` and
     `command_cycles_per_wave=0,8,32` in the same composed dual-stream
     reduced-replica recost path. It is intentionally dependency-gated behind
     the exp-LUT quality gate, exp-LUT L1 PPA, and the base exp-LUT recost.
   - Remaining work: run this job only after the exp-LUT quality/PPA chain
     materializes. It is still a cycle-sensitivity model for scheduler/control
     overhead, not measured command-distribution RTL.
   - Follow-on measurement path: `prop_l1_decoder_attention_command_dispatch_control_v1`
     adds a central command-dispatch RTL microblock for 8/16/32 clusters. This
     can later replace or bound the per-tile/per-wave command-cycle sensitivity
     with measured control PPA, while leaving distributed control fanout as an
     explicit remaining abstraction.
   - Follow-on recost path:
     `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_measured_command_control_llama7b_v1`
     consumes the L1 command-dispatch-control PPA and charges the selected
     measured central control variant into the score32 exp-LUT reduced-replica
     Llama7B recost.

7. Integrated schedule closure audit
   - Scope: rerun the Llama7B attention schedule with measured compute,
     full-value tile, softmax, SRAM, NoC, HBM, and precision evidence.
   - Status: merged by PR #963. The surviving abstractions are now explicit:
     HBM/DRAM service, NoC/SRAM service contention, full integrated energy,
     q12/PWL dual-stream area/clock promotion, and KV4 precision recovery.

## Ordering

The current first step is to unblock the remote evaluator source checkout and
run the already queued exp-LUT branch:

1. Run `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`.
   This decides whether the replacement score32 exp-LUT divider path is
   quality-backed.
2. Run `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1`.
   This measures the matching composed RTL wrapper PPA.
3. If both inputs pass/materialize, release
   `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1`
   to recost the Llama7B point. Its first command now runs
   `npu/eval/check_attention_exp_lut_frontier_release.py`; if that release gate
   fails, do not run or promote the exp-LUT recost row as quality-backed. Return
   to the softmax replacement design or another score32/w16 implementation.
4. Run
   `l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1`
   to close the reduced-replica-to-measured-wrapper promotion audit. This is
   complete: PR #1197 records a wrapper metrics match and no required
   partitioned/cluster wrapper validation.
5. Run
   `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1` to record
   the measured/inherited service provenance of the promoted score32 exp-LUT
   row. This is complete: PR #1199 records score32 support and identifies
   SRAM capacity placement plus HBM/DRAM service as the remaining service
   abstractions.
6. Run
   `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`
   to replace the ideal shared-SRAM packing estimate with an explicit SRAM
   macro placement-efficiency envelope. This is complete: PR #1201 records a
   stable score32 frontier under the explicit SRAM macro placement-efficiency
   envelope.
7. Run
   `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`
   to close the inherited HBM/DRAM service abstraction for the score32 exp-LUT
   row. The job should combine the score32 SRAM envelope, measured
   command-control row, and command-calibrated HBM pJ terms, then report
   latency, throughput, HBM energy, compute energy, total energy, and remaining
   controller/signoff abstractions. This is complete: PR #1203 records the
   score32 row as HBM-sensitive but keeps the same latency-scale frontier.
8. Run
   `l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1` to
   rank the closed score32 row against the prior integrated, measured
   exact-FP16, and mixed/int8 evidence. The result should explicitly distinguish
   promotable precision-safe rows from planning-only or quality-unclosed rows,
   then identify the current throughput frontier, energy reference, and next
   architecture target. This is complete: PR #1205 records score32 as the
   precision-safe throughput frontier and measured exact-FP16 as the energy
   reference.
9. Run
   `l2_decoder_attention_score32_compute_activity_energy_llama7b_v1` to close
   the score32 wall-time compute-energy ambiguity. The result should derive
   compute active duty from the measured command-control cycle fields, sweep
   idle-power fractions, and state whether clock-gating/active-cycle accounting
   can close the score32 energy gap. This is complete: PR #1209 records that
   score32 remains energy-worse after ideal clock-gating bounds.
10. Run
    `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_ppa_v1`
    to measure reduced-parallel score32 exp-LUT composed wrapper variants
    (`8x8`, `8x4`, and `4x4`) against the current `16x8` wrapper. This closes
    the immediate circuit-level question left by the activity audit: whether
    lower local parallelism can materially reduce score32 power/area.
11. After the L1 parallelism metrics merge, run
    `l2_decoder_attention_composed_datapath_score32_exp_lut_div_parallelism_recost_llama7b_v1`.
    This recost must consume each wrapper's generated manifest/config
    `total_macs` so latency, replica count, area, and energy are not
    accidentally inherited from the full `16x8` wrapper. This is complete:
    PR #1213 records the `8x8 ppc1` measured wrapper as the selected local
    point and keeps `12322.504989 us/token` as the recosted feasible latency.
12. Run
    `l1_decoder_attention_dual_stream_schedule_wrapper_score32_exp_lut_ppa_v1`
    to measure bounded c2/c4 score32 exp-LUT schedule-wrapper slices. This
    reduces the remaining scheduler/control abstraction by putting central
    dispatch, local ready/valid issue, local completion accounting, and the
    selected composed datapath replicas into one measured RTL/PPA wrapper. The
    follow-on L2 item is
    `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`.
    It should scale from this wrapper evidence and keep external SRAM, NoC,
    HBM/DRAM service, and full-array physical signoff as explicit remaining
    abstractions.
13. Run
    `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1`
    against the full 856-producer, sixteen-cluster SRAM, local-reducer, and
    finalized-tree composition. Require exact aggregate and per-cluster
    traffic counts, zero sticky errors, and structured equality for every
    cluster and root row. Timeout or OOM is inconclusive; an arithmetic,
    ordering, metadata, or protocol mismatch is conclusive.
14. After the equivalence artifact merges, recost the Llama7B score32 point
    with the measured command-to-root service interval and measured SRAM
    request/fill traffic. Do not treat deterministic fill arrival as measured
    HBM service, and do not charge inferred SRAM as a characterized macro.
15. Close the remaining communication and physical abstractions with a
    logically valid mesh topology/scheduler pair, SRAM macro PPA substitution,
    and utilization-matched cluster-array physical slices. Rerank token
    throughput, energy, area, and precision only after each substituted term
    names its measured source and leaves no incompatible category mixed into
    the same rank.
16. Recover or rerun `l1_segmented_xy_router_node5_bare_ppa_v1` after router
    r7. Require all 40/50/60 percent utilization rows at 1.8 ns, exact isolated
    flow variants, complete finite PPA, retained routed artifacts, and explicit
    register-to-register setup-path identity. A stale lease or one accepted row
    is not enough to satisfy this gate.
17. After the bare-router result merges, run
    `l2_decoder_attention_score32_noc_exact_router_postroute_activity_power_llama7b_v2`.
    Regenerate and cycle-verify all five exact transport phases on the remote
    evaluator. Require phase cardinality gates, physical-top source identity,
    unique effective flow variants, direct VCD annotation, timing feasibility,
    and at least 95 percent sequential-register sidecar coverage. Keep the
    result as intrinsic router energy; it excludes aggregate links, mesh clock
    tree, endpoint/SRAM activity, and HBM/DRAM.
18. Run `l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r4` from its clean isolated
    flow and retain new failure evidence if it does not route. If successful,
    use its routed dimensions and reports to derive the replacement composed
    endpoint/mesh floorplan rather than reusing the retired 3.2 mm envelope.
    This aggregate result measures canonical routers plus inter-router links
    and clock distribution, but not endpoint/SRAM logic.
19. Prove endpoint r4 setup-path identity or run an independently registered
    replacement, then create the new composed endpoint/mesh PPA and exact
    activity jobs. Only those measurements can replace vectorless/scaled NoC
    and endpoint energy in the Llama7B frontier. The merged shared-mesh replay
    now embodies simultaneous VC0/VC1 arbitration and cycle-checks every
    endpoint decision, but its remote evaluator result is still pending.
20. Run the exact p54/p53 release-cadence item and its dependent common-clock,
    one-held-beat, stall-dilated shared-mesh replay on the remote evaluator.
    Preserve separate VC0 and VC1 completion and do not interpret the result
    as complete dataflow closure.
21. Implement `prop_l1_attention_score32_exact_kv_ingress_assembler_v1` from
    the canonical K/V layout. Require a checked address decoder, planar gather
    descriptors for partial resident ranges, partial-byte
    validity, a 1 KiB token-major-to-fill-row V transpose buffer, and a 2 KiB
    paired-stream p53/p54 K transpose buffer. A sequential 256-bit V flit
    contributes to four different fill rows, so payload-width equality cannot
    substitute for this reorder logic. Prove every byte maps bijectively to
    the existing cluster SRAM and producer interfaces under arbitrary
    backpressure.
22. Compose the ingress block with capacity-driven resident descriptors,
    transient HBM-return source selection, shared-mesh routing, cluster
    double-buffer residency, and producer release. Measure representative
    physical slices remotely; keep the external HBM controller/PHY and SRAM
    bitcells as disclosed boundaries.
23. Replace the historical VC0 capacity bound with the composed exact ingress
    cycles and measured component PPA, then rerank the Llama7B candidates by
    token throughput, energy, area, and precision. No candidate can be called
    the confidence-bounded best architecture before this substitution passes
    workload equivalence and evidence-category checks.

All new evaluation jobs should run on the remote evaluator
`eval-daemon-b7c2d9c80c1c`, not the devcontainer.
