# Quality Gate

- Staged FIFO, router, mesh, and functional-wrapper sources are byte-identical
  to canonical RTL sources.
- The wrapper adds no behavior, instantiates exactly one mesh, and exposes no
  debug-counter ports.
- Yosys hierarchy elaboration retains router instances 0 through 15.
- Yosys processing with `ENABLE_DEBUG_COUNTERS=0` proves that all debug-counter
  registers are pruned while transport state remains.
- The declared 8,962-pin interface and 1.12 um/pin bound fit within the declared
  3.2 mm square die perimeter.
- Existing canonical full-mesh RTL tests remain green; the wrapper cannot alter
  functional ready/valid, flit, or routing behavior.
