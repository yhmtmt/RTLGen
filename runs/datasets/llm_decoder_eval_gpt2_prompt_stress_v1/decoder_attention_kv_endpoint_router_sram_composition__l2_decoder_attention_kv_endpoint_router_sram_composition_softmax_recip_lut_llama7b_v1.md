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
- endpoint_width_ratio_vs_measured_ppa: `8`
- tile_sram_capacity_fraction_of_selected_local_capacity: `0.032113`
- tile_sram_budget_area_fraction: `0.142156`

## Closure Flags
- ready_valid_endpoint_passed: `True`
- endpoint_ppa_width_matches_ready_valid_width: `False`
- router_ppa_width_matches_link_width: `False`
- fifo_ppa_width_matches_link_width: `False`
- tile_sram_profile_fits_sram_area_budget: `True`
- tile_sram_capacity_covers_selected_local_capacity: `False`

## Decision
- decision: `composition_requires_follow_on_ppa`
- required_follow_on_ppa: `endpoint_ppa_width_matches_ready_valid_width, router_ppa_width_matches_link_width, fifo_ppa_width_matches_link_width, full_local_capacity_sram_macro_profile_missing`

## Recommended L1 Points
- `onchip_service_endpoint`: ready/valid probe used DATA_W=1024 but selected PPA currently references w128 endpoint metrics
- `noc_router`: selected link is 2048 bits but current PPA references w128 router metrics
- `noc_fifo`: selected link is 2048 bits but current PPA references w128 FIFO metrics
- `local_sram_capacity`: tile-local SRAM buffers are measured, but the selected local-capacity pool is still capacity-estimated

## Remaining Abstractions
- Router/FIFO PPA is lane-scaled from narrower measured primitives until wide-link L1 points are measured.
- Endpoint ready/valid behavior is verified at 1024 bits, but endpoint PPA is still from the existing w128 wrapper.
- Tile-local SRAM buffers have CACTI metrics, but the selected per-cluster local capacity pool is not yet a concrete SRAM macro set.
- HBM/DRAM service remains inherited and intentionally outside this audit.
