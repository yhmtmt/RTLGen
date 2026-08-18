# Design Brief

The prior schedule emits 8,320 reduction bytes per cluster after every tile
wave. That quantity assumes 16-bit reduction scalars. The embodied exact local
temporal reducer instead accumulates eight waves and emits 128 structured
419-bit beats for each of four eight-head groups.

The revision compares three lossless transports over the existing 256-bit
flit: direct two-flit beat alignment, contiguous group bit packing, and an
ordered stats-once format that transmits each head's 32-bit maximum and 33-bit
sum once while retaining every 41-bit numerator. Metadata in the stats-once
format is reconstructed from the already checked group/head/slice order.
