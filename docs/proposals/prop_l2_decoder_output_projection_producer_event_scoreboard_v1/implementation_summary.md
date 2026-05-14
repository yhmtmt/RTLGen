# Implementation Summary

Replaces the wide `event_state[65535:0]` vector in `npu/rtlgen/gen.py` with a bounded associative EVENT scoreboard controlled by `event_scoreboard_entries`.

Updates EVENT_SIGNAL to insert or refresh a scoreboard entry, and EVENT_WAIT to latch the event id then clear the matching scoreboard entry when it appears.

Updates RTL shell diagnostics and generator tests to reference the bounded scoreboard and confirm no production generated RTL contains `event_state`.
