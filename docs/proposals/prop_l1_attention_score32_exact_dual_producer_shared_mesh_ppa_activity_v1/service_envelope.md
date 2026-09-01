# Exact Shared-Mesh Standalone Service Envelope

- total exact traffic: `70948` flits
- joint completion: `15769` cycles
- VC0 completion: `15769` cycles
- VC1 completion: `10219` cycles
- source compute layer: `421511.3976` ns
- maximum composed clock for standalone capacity fit: `26.730382244` ns

This is a finite standalone capacity bound, not a producer-coupled throughput result.

## Proves

- one embodied shared mesh can drain the full exact layer traffic without artificial sink stalls
- VC0 and VC1 overlap, arbitrate, contend, and complete with exact payload integrity
- the measured physical clock can be compared to a finite standalone capacity threshold

## Does Not Prove

- producer-release-coupled layer completion or overlap with compute
- workload-annotated physical power or token energy
- vendor HBM timing or energy

## Next Gate

Replay the same embodied service with VC0 residency events and VC1 group releases timed by the actual compute/reducer valid-ready schedule; then compare its final completion to the compute layer window.
