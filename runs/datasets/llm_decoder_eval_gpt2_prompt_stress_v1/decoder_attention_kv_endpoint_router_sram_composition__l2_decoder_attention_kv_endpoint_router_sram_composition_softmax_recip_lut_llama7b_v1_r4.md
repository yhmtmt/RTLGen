# Endpoint Router/SRAM Composition Audit

## Selected Frontier
- latency_us: `3222.903773`
- topology: `mesh2d`
- clusters: `16`
- banks: `64`
- link_width_bits: `2048`
- packet_payload_bytes: `128`
- dominant_tile_resource: `shared_path`

## Composition Quantities
- packet_bits: `1024`
- router_lanes_for_packet: `4`
- router_lanes_for_link: `8`
- fifo_lanes_for_link: `8`
- endpoint_width_ratio_vs_measured_ppa: `1`
- tile_sram_capacity_fraction_of_selected_local_capacity: `0.032113`
- tile_sram_budget_area_fraction: `0.142156`

## Closure Flags
- ready_valid_endpoint_passed: `True`
- endpoint_ppa_width_matches_ready_valid_width: `True`
- router_ppa_width_matches_link_width: `False`
- fifo_ppa_width_matches_link_width: `False`
- tile_sram_profile_fits_sram_area_budget: `True`
- tile_sram_capacity_covers_selected_local_capacity: `False`

## Closure Diagnosis
- endpoint: `measured_at_ready_valid_width`
- router: `lane_composed_segmented_evidence_available_while_flat_2048_failed`
- fifo: `lane_composed_segmented_evidence_available_while_flat_2048_failed`
- local_sram_capacity: `local_capacity_budget_failed`

## Local SRAM Capacity Budget
- fits_sram_budget: `False`
- total_area_um2: `1306824061.5888963`
- sram_budget_area_um2: `280000000.0`
- area_fraction_of_sram_budget: `4.667229`

## Decision
- decision: `composition_requires_follow_on_ppa`
- required_follow_on_ppa: `capacity_rebalance_or_smaller_local_sram_required`

## Recommended L1 Points
- `local_sram_capacity`: tile-local SRAM buffers are measured, and local-capacity CACTI evidence is available; re-balance or reduce the selected local-capacity pool to resolve a local SRAM budget failure.

## Remaining Abstractions
- Lane-composed/segmented NoC PPA metrics are available for router/FIFO while flat 2048-bit boundary evidence failed.
- Tile-local SRAM buffers are measured, but measured local-capacity evidence already shows the selected per-cluster local SRAM pool exceeds the available shared SRAM budget.
- HBM/DRAM service remains inherited and intentionally outside this audit.
