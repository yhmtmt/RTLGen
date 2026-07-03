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
  - the active follow-on branch is the score32 exp-LUT divider path:
    `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1`
    and
    `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`
    are queued. The dependent recost
    `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1`
    is intentionally blocked until both inputs are materialized.
- New evaluations should continue to dispatch only to the remote evaluator
  `eval-daemon-b7c2d9c80c1c`, not the devcontainer.

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
     recost only if the quality gate passes and the measured PPA row is
     materialized.

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
   to recost the Llama7B point. If the quality gate fails, do not promote the
   exp-LUT row as quality-backed; return to the softmax replacement design.
4. In parallel with evaluator recovery or after exp-LUT recost, prepare the
   command-overhead sensitivity job for the selected dual-stream schedule. This
   preparation is complete as of PR #1119; the item should remain blocked until
   the exp-LUT quality/PPA/base-recost dependencies are merged and materialized.
5. After the exp-LUT inputs are running or complete, dispatch
   `l1_decoder_attention_command_dispatch_control_ppa_v1` to measure the
   central scheduler/control block that will bound the command-cycle
   sensitivity model. Do not let it displace the already READY exp-LUT quality
   and PPA jobs.
6. After the L1 command-control PPA and exp-LUT recost materialize, run
   `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1`
   to charge measured central control area/power/clock into the same Llama7B
   reduced-replica point.

All new evaluation jobs should run on the remote evaluator
`eval-daemon-b7c2d9c80c1c`, not the devcontainer.
