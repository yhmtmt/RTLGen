# Promotion Gate

Promotion requires the merged remote JSON and Markdown artifacts with:

- `coverage=workload_complete`
- all packet/flit equivalence flags true
- exact cycle and router counter agreement
- zero endpoint protocol errors
- finite queue/context parameters recorded
- remaining physical abstractions preserved

Passing this gate permits replacing the logical release-queue timing with the
finite endpoint cadence in the next composed PPA rerank. It does not promote
SRAM, scheduler, activity power, or HBM/DRAM closure.
