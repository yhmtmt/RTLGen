# Evaluation Gate

Require the complete model/RTL equivalence suite and generated-artifact guard
before OpenROAD.  Reject a physical result if payload storage is optimized
away, structural checks fail, or harness logic dominates the mapped hierarchy.
Run the six requested periods at placement density 0.50 and record infeasible
timing or placement points explicitly.  Keep scheduler standard-cell PPA,
shared-SRAM macro area/access energy, downstream arithmetic, and HBM/DRAM as
separate quantities.
