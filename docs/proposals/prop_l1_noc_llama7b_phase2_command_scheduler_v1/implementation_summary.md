# Implementation Summary

- Added synthesizable wave/class/cluster/packet command generation RTL.
- Replaced global packet-ID-derived payload addresses with fixed shared,
  reduction-source, and source-indexed root-reduction packet slots.
- Proved every generated command against the independently built Python
  schedule under output backpressure.
- Added a generated-command option to the scheduler physical harness and
  direct design generator.
- Added a Nangate45 macro sweep directly comparable with the earlier
  SRAM-prefetch scheduler point.
