# Implementation Summary

Stages EVENT_WAIT retirement in `npu/rtlgen/gen.py` by latching `event_wait_id`, holding `event_wait_pending`, and servicing the wait before fetching the next command.

Updates the RTL shell event-DMA testbench to wait for the second DMA issue instead of treating the EVENT IRQ from EVENT_SIGNAL as proof that EVENT_WAIT already retired.

Adds `tests/test_npu_rtlgen_event_wait.py` to guard the generated full and diagnostic EVENT_WAIT paths.
