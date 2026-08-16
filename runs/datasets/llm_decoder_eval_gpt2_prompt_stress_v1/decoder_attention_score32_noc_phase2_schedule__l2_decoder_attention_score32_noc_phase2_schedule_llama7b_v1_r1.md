# Llama7B Score32 NoC Phase 2 Schedule

## Source Contract

- source recost: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_recost__l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json`
- measured L1 cost file: `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_endpoint_v1.json`
- measured L1 profile: `hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10`
- coverage: `workload_complete`
- declared waves: `8`
- simulated waves: `8`
- compute clock: `48.6509 ns`
- NoC clock: `1.0 ns`

## Mapping

- cluster endpoints: `0(0,0), 1(1,0), 2(2,0), 3(3,0), 4(0,1), 5(1,1), 6(2,1), 7(3,1), 8(0,2), 9(1,2), 10(2,2), 11(3,2), 12(0,3), 13(1,3), 14(2,3), 15(3,3)`
- root endpoint: `15(3,3)`
- shared-SRAM stride/offset: `3` / `1`
- shared-SRAM observed average/worst hops: `3.0` / `6`

## Traffic

- full tile bytes: `1048576`
- shared tile bytes: `17408`
- local tile bytes: `1031168`
- reduction bytes per cluster-wave: `8320`
- simulated tiles: `128`

## Routed Result

- drain cycles: `397004`
- drain time: `397004.0 ns`
- source compute-layer envelope: `421511.3976 ns`
- drain within source compute-layer envelope: `True`
- scheduled packets: `11576`
- scheduled flits: `92128`
- contention cycles: `36747`
- max router input occupancy: `16`
- total endpoint input stall cycles: `319772`

## Tag Semantics

- collision-free reuse proven: `True`
- 8-bit tag reuse invariant: `Concrete low_tag = tuple packet sequence index mod 256. For every reused (source, destination, vc, low_tag), the next packet's first injection cycle is strictly greater than the prior packet's last delivery cycle; same-cycle reuse is treated as ambiguous and rejected.`
- ordered tuple stream proven: `True`
- max packets per tuple: `264`

## Assumptions

- Producer compute, local SRAM access, and local reducer accumulation stay intra-cluster and do not consume the mesh in this Phase 2 schedule.
- Only two remote traffic classes are routed: shared SRAM tile payloads and local-reducer-to-root partial reductions.
- Tile-to-cluster assignment is static wave-major round robin over the named cluster endpoints.
- Shared SRAM homes use a deterministic rotating stride/offset mapping chosen only from explicit 4x4 permutations to approximate the declared hop envelope while keeping load balanced.
- The root endpoint is explicit and fixed; root-finalizer output remains local to that endpoint.
- Wave start and reduction release times are derived from checked-in score32 compute cycles and converted to absolute NoC cycles using the explicit compute and NoC clock periods.
- HBM/DRAM timing is intentionally excluded; no remote traffic or timing claim is made for HBM service.
- Each packet carries up to packet_payload_bytes of payload and is segmented into 256-bit flits with no extra header flit modeled.
- The performance model does not perform packet reassembly; the checked artifact therefore fails closed unless 8-bit tag reuse is provably non-overlapping for each (source, destination, vc) tuple over packet lifetime intervals.
- Per-endpoint release queues are logical zero-copy descriptors over payloads retained in source SRAM or reducer state, not physically costed flit FIFOs; endpoint packetizer/control storage remains outside this result.

## Remaining Abstractions

- The schedule uses clock-corrected static wave timing from checked-in recost quantities and does not yet prove end-to-end command/control RTL cadence.
- The NoC clock is an explicit evaluation assumption until the exact five-port segmented-router physical result is merged and substituted.
- The source-descriptor queues and producer backpressure/control needed to retain payloads until injection are not yet embodied or physically measured.
- Shared SRAM home placement is deterministic and explicit, but still a topology adapter rather than a measured SRAM floorplan.
- HBM/DRAM service and controller timing remain intentionally out of scope.
- Root-finalizer internal compute is not rerouted here; the mesh model stops at root ingress.
