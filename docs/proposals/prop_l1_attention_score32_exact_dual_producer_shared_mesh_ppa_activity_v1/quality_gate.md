# Quality Gate

- Preserve exact score32 arithmetic and the existing Llama7B quality result.
- Preserve all 60,928 VC0 and 10,020 VC1 flits with zero protocol errors.
- Preserve four sequential VC1 group lifecycles and 512 exact checked rows.
- Require one shared mesh, sixteen endpoint arbiters, and zero private meshes.
- Require every endpoint arbitration decision to match the independent cycle
  model across the complete simultaneous workload.
- Keep the eager-producer service envelope separate from producer-coupled
  throughput evidence.
- Do not infer token energy from vectorless whole-harness power.
- Keep HBM/DRAM explicitly external.
