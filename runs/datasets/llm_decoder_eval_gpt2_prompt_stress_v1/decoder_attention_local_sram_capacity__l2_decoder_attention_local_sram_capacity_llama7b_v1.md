# Llama7B Local SRAM Capacity Profile

## Selected Frontier
- active_clusters: `16`
- local_capacity_bytes_per_cluster: `19140624`
- local_sram_fraction: `0.25`
- sram_area_fraction: `0.35`

## Chunking
- width_bits: `1024`
- chunk_count_per_cluster: `4`
- allocated_bytes_per_cluster: `19152896`
- capacity_overhead: `1.000641`
- chunks_bytes: `[16777216, 2097152, 262144, 16384]`

## Budget
- total_area_um2: `1306824061.5888963`
- sram_budget_area_um2: `280000000.0`
- area_fraction_of_sram_budget: `4.667229`
- fits_sram_budget: `False`

## Remaining Abstractions
- CACTI estimates are macro-level SRAM access/energy estimates, not a placed SRAM compiler floorplan.
- The profile models local-capacity SRAM chunks only; HBM/DRAM service remains separate.
- NoC arbitration and endpoint/router PPA are measured by separate closure items.
