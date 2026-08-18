# Quality Gate

- No numerator may be narrowed below signed 41 bits.
- Maximum and sum state must remain 32 and 33 bits.
- Stats-once metadata reconstruction is legal only for the checked ordered
  eight-head, sixteen-slice group stream.
- Do not claim cycle closure before actual producer and root ready/valid
  interfaces are composed.
