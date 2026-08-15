# Design Brief

The consumer validates the canonical schedule and exact composed promotion,
uses `max(source_clock, composed_critical_path)` because SRAM macro timing is
outside the wrapper, reruns all eight waves and 128 tiles, and records the
placed footprint, vectorless power, and diagnostic drain energy.
