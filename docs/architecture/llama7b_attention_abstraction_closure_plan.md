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
- There is no active queue item for this closure stage. New evaluations should
  continue to dispatch only to the remote evaluator
  `eval-daemon-b7c2d9c80c1c`.

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

2. HBM/DRAM and on-chip service detail
   - Scope: replace aggregate HBM efficiency and compact NoC/SRAM service caps
     with a more explicit controller, arbitration, and contention model.
   - Status: partially bounded by the HBM energy sensitivity result, the merged
     HBM/DRAM command-service energy result, and the source-backed aggregate HBM
     energy calibration result, but not cycle-accurate. The aggregate
     source-backed calibration preserved the selected family but changed the
     dominant component to HBM.
   - Next result: run
     `l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1`,
     consuming the merged HBM/DRAM service-energy result and source-backed HBM
     energy calibration result, to retain command-mix and row-hit sensitivity
     while calibrating to the HBM2 aggregate pJ/bit anchor.

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

7. Integrated schedule closure audit
   - Scope: rerun the Llama7B attention schedule with measured compute,
     full-value tile, softmax, SRAM, NoC, HBM, and precision evidence.
   - Status: merged by PR #963. The surviving abstractions are now explicit:
     HBM/DRAM service, NoC/SRAM service contention, full integrated energy,
     q12/PWL dual-stream area/clock promotion, and KV4 precision recovery.

## Ordering

The next evaluation should keep closing the dominant HBM term while preserving
command-mix sensitivity. The merged source-backed HBM calibration shows the
selected family is stable, but HBM dominates energy. The next job should scale
the command-class HBM/DRAM service model to the HBM2 aggregate pJ/bit anchor and
sweep row-hit sensitivity. After that, directly measure or bound the selected
compute service point if the command-calibrated HBM result preserves the selected
family. All new evaluation jobs should run on the remote evaluator, not the
devcontainer.
