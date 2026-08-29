# Exact Mixed-VC Router Arbitration Envelope

This proposal places the validated 60,928-flit VC0 shared-SRAM phase and four
2,505-flit VC1 exact-reduction phases on one 4x4 mesh. It sweeps the missing
producer-relative release time and reports the source buffering required by
each shared-mesh overlap point.

The envelope must not promote a raw low-cycle row when isolated producer
traces accumulated more than one flit behind the shared endpoint arbiter.
