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
- router_lanes_for_packet: `8`
- router_lanes_for_link: `16`
- fifo_lanes_for_link: `16`
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
- router: `flat_link_width_boundary_failed`
- fifo: `flat_link_width_boundary_failed`
- local_sram_capacity: `full_local_capacity_sram_macro_profile_missing`

## Decision
- decision: `composition_requires_follow_on_ppa`
- required_follow_on_ppa: `segmented_or_narrower_router_ppa_required, segmented_or_narrower_fifo_ppa_required, full_local_capacity_sram_macro_profile_missing`

## Recommended L1 Points
- `segmented_noc_router`: flat 2048-bit router failed physical boundary runs; measure lane-composed or narrower-link router/scheduler pairs instead of retrying the same flat primitive
- `segmented_noc_fifo`: flat 2048-bit FIFO failed physical boundary runs; measure lane-composed or narrower-link FIFO/scheduler pairs instead of retrying the same flat primitive
- `local_sram_capacity`: tile-local SRAM buffers are measured, but the selected local-capacity pool is still capacity-estimated

## Remaining Abstractions
- Router/FIFO PPA cannot use the failed flat 2048-bit primitive; lane-composed or narrower-link NoC PPA remains open.
- Tile-local SRAM buffers have CACTI metrics, but the selected per-cluster local capacity pool is not yet a concrete SRAM macro set.
- HBM/DRAM service remains inherited and intentionally outside this audit.
