# Evaluation Gate

- Run only after router r7 and the fresh aggregate 4x4 r2 physical baseline are
  merged; the stale-cache-invalid v1 result is not a dependency.
- Use the exact canonical FIFO, router, mesh, and logic-free functional wrapper
  sources.
- Require all sixteen generated router instances at elaboration and reject
  source/profile or pin-perimeter drift before OpenROAD.
- Use an independently isolated ORFS flow variant at 2.0 ns in the same 3.2 mm,
  45 percent density feasibility envelope as the aggregate baseline.
- Require complete timing, die area, power, and retained path evidence for a
  promotable row; preserve explicit bounded failures.
- Treat vectorless power as physical completion evidence only. Workload energy
  requires a hierarchy-matched Llama7B activity run.
