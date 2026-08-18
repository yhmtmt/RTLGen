# Design Brief

The controller holds one command containing release cycle, source,
destination, VC, tag, TX/RX base addresses, and flit count. After release it
holds the destination RX descriptor until accepted, then holds the source TX
descriptor until accepted. A completing TX may be replaced by the next command
on the same edge. This gives a deterministic minimum cadence of two cycles per
packet without allowing packet arrival to race RX context allocation.

The command record is 102 bits (`32+4+4+2+8+24+24+4`). A concrete prefetch
controller issues sequential SRAM addresses, permits one outstanding read,
holds one returned record, and overlaps the next read with command acceptance.
Its backing SRAM bitcells are not implemented as flops in this block; capacity
and macro energy are reported and costed separately. Command population and
inter-wave refill remain an explicit producer boundary for follow-on closure.
