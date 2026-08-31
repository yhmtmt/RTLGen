# Design Brief

The compact 163-pin top contains both exact activity producers. VC0 embodies
the complete 112-context admission/engine/endpoint service. VC1 embodies four
sequential exact stats-once groups, packet adapters, shared-root storage,
decoder, and the c16/r2/l8/b59 final tree. Both private meshes are disabled.

Sixteen held-grant arbiters merge the producer streams into one segmented 4x4
mesh. Ejection is demultiplexed by VC with producer-specific backpressure and
fail-closed protocol errors.

Reusable area is the disjoint sum of:

- `composition/vc0_activity/service/`
- `composition/vc1_activity/exact_transport_wrapper/`
- `composition/shared_transport/`

Activity generation outside those prefixes is not reusable DUT area.
