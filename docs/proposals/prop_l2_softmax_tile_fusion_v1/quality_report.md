# Terminal Softmax Quality Precheck

- status: pass
- scope: `terminal_softmax_routing_only`

## Inputs
- `onnx_path`: `/workspaces/RTLGen/runs/model_cache/onnx_imported_softmax_tail_v1/logistic_regression.onnx`
- `baseline_arch`: `/workspaces/RTLGen/npu/arch/examples/minimal.yml`
- `candidate_arch`: `/workspaces/RTLGen/npu/arch/examples/minimal_softmax_tail_fused.yml`
- `perf_config`: `/workspaces/RTLGen/npu/sim/perf/example_config_fp16_cpp.json`
- `batch_override`: `256`

## Summary
- `baseline_event_target`: `dma_y`
- `candidate_event_target`: `softmax1`
- `baseline_softmax_dst`: `ACT_A_SRAM`
- `candidate_softmax_dst`: `Y_DRAM`
- `baseline_dma_ops`: `4`
- `candidate_dma_ops`: `3`
- `baseline_total_bytes`: `2572`
- `candidate_total_bytes`: `1548`
- `removed_dma_bytes`: `1024`
- `baseline_schedule`: `docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report_artifacts/baseline_schedule.yml`
- `candidate_schedule`: `docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report_artifacts/candidate_schedule.yml`
- `baseline_descriptors`: `docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report_artifacts/baseline_descriptors.bin`
- `candidate_descriptors`: `docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report_artifacts/candidate_descriptors.bin`
- `baseline_trace`: `docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report_artifacts/baseline_trace.json`
- `candidate_trace`: `docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report_artifacts/candidate_trace.json`

## Checks
- `pre_softmax_ops_match`: op dma_x/dma_w1/dma_b1/gemm1 identical
- `terminal_softmax_params_match`: softmax src/row_bytes/rows/dtype unchanged
- `routing_only_delta`: candidate routes softmax directly to Y_DRAM and removes dma_y
- `perf_delta_bounded`: perf trace removes exactly one DMA op and one dma_y byte transfer

## Failures
- none
