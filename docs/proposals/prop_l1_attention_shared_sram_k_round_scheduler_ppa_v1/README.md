# Shared-SRAM K round scheduler PPA

This package measures the physically bank-ordered, double-buffered K-prefetch
scheduler for one Llama7B GQA8 KV head.  It replaces the synthesis-intractable
two-by-16-KiB full-window register point with two 17-word windows.

The functional gate compares the executable performance model and RTL across
all 1,024 requests, responses, and compute beats.  It checks the exact
block-major stride-8 address layout, 17-bank routing, final nine-word round,
backpressure, and fail-closed response metadata.

The physical harness retains all 34,816 live payload bits and narrows only the
top-level pins.  Its checksum prevents dead-output removal for activity/PPA;
it is explicitly not equivalence evidence.  The run excludes full shared-SRAM
capacity area/access energy, downstream score arithmetic, and external
HBM/DRAM.

The synthetic response source derives one 64-bit lane from request metadata
and replicates it across the 1024-bit word.  This keeps all payload registers
active without synthesizing seventeen wide arithmetic stimulus generators.
The small narrow-I/O harness overhead remains included and is identified in
the generated manifest.

As a bounded preflight, the complete hierarchy passes Nangate45 generic
technology mapping and post-map structural checks in 152.43 seconds at 2.223
GiB peak RSS.  The resulting 403,922.862 um2 estimate is pre-route evidence
only; this proposal's OpenROAD sweep is the physical calibration authority.
The 1,000-by-1,000 um core uses placement density 0.50: the pre-route DUT
estimate alone is 40.39% of core area, so the former 0.40 setting had no margin
for harness and implementation cells.

The generated top also passes bounded Nangate45 mapping with zero structural
problems.  It retains all 34,816 payload flip-flops and estimates 414,621.116
um2 total area.  The 10,698.254 um2 difference from the bare hierarchy is 2.58%
explicit harness overhead, and total pre-route core utilization is 41.46%.

The full-window point remains recorded as functionally valid but
`synthesis_infeasible_flat_register_window`.  It must not be ranked using the
round point's PPA.
