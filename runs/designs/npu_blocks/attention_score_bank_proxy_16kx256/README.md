# attention_score_bank_proxy_16kx256

This design maps one logical 16Kx256 synchronous 1RW score bank onto 56
`fakeram45_2048x39` macros: eight depth groups and seven parallel width slices.

The installed Nangate45 FakeRAM provides LEF and Liberty views but no GDS.
Results from this design measure proxy floorplan, routing, timing, and standard
cell banking overhead. They are not SRAM implementation signoff.
