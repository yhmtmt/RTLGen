# Design Brief

A complete 128-word K window gives a 128-cycle compute interface but expands
two 16 KiB windows into synthesis-intractable register state.  The round
scheduler stores only one 17-bank conflict-free round in each of two buffers,
then emits sixteen dimension beats before reusing the buffer.  This retains
the exact 1,024 shared-SRAM requests while trading the interface schedule to
1,024 compute beats and reducing live storage to 34,816 bits.

Storage is physically bank ordered.  Tagged responses write a fixed bank leaf,
and the compute side applies the bounded bank permutation.  Full macro capacity
and access energy, score arithmetic, NoC, and external DRAM are composed
separately.
