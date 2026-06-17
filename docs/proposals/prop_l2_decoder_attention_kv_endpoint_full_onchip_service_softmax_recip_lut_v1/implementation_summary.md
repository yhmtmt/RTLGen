# Implementation Summary

- Added after PR #877 so `softmax_recip_lut` endpoint full on-chip service jobs consume the corrected q8/q10/q12 full-search source.
- The requested item keeps HBM/DRAM inherited unchanged and only refines on-chip SRAM/NoC service scheduling.

