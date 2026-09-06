# Llama7B Score32 Cadence/Frontier Consistency Audit

- decision: `recorded_score32_latency_retracted_pending_cadence_integrated_recost`
- recorded two-point Pareto set physically credible: `False`
- superseded Score32 latency: `12814.258 us`
- strict serialized sensitivity before RMSNorm: `43514.922 us`
- strict serialized sensitivity with RMSNorm: `44187.672--45620.922 us`
- nearest measured reference latency: `72544.062 us`
- conservative latency lead preserved: `True`
- claim scope: conservative timing sensitivity only; energy and area are not recost

## Blockers

- the integrated frontier still consumes the superseded 986-cycle tile-service term
- the local 53/54-way persistent reducer and safe group overlap scheduler remain unresolved
- score32 energy has not been recomputed for the corrected service time or closed with activity
