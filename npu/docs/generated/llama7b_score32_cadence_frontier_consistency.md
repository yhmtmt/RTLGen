# Llama7B Score32 Cadence/Frontier Consistency Audit

- decision: `recorded_score32_latency_retracted_pending_cadence_integrated_recost`
- recorded two-point Pareto set physically credible: `False`
- superseded Score32 latency: `12814.258 us`
- single-clock interval before RMSNorm: `146083.474--172387.653 us`
- dual-clock interval before RMSNorm: `29360.931--50588.451 us`
- dual-clock interval with serialized RMSNorm: `30033.681--52694.451 us`
- nearest measured reference latency: `72544.062 us`
- dual-clock latency lead preserved: `True`
- claim scope: measured reducer service and component-area bounds; no routed composed top, CDC closure, or activity-backed energy

## Blockers

- the integrated frontier still consumes the superseded 986-cycle tile-service term
- the routed 53/54-way composed top is absent despite functional reducer and routed submacro evidence
- the latency-leading dual-clock interval requires unmeasured CDC and scheduler composition
- score32 energy has not been recomputed for the measured reducer schedule or closed with activity
