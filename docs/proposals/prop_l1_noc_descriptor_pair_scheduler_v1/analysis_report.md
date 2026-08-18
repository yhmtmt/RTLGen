# Analysis Report

Measured PPA is pending. Functional evidence establishes one RX and one TX
handshake per valid command with a two-cycle minimum issue cadence.

The complete local Llama7B replay drained 11,576 packets and 92,128 flits in
397,227 cycles with exact RTL/performance agreement. This is 24 cycles slower
than the merged endpoint-parallel issuer result, while router contention fell
from 30,285 to 8,736 cycles, input stalls from 46,504 to 11,816 cycles, and
peak router occupancy from 11 to 7.
