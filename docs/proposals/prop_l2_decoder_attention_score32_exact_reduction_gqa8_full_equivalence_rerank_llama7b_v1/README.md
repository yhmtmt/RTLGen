# Score32 Exact-Reduction Full-GQA8 Rerank

This proposal adds a bounded L2 rerank/recost step that consumes four existing
artifacts only:

- the materialized score32 exact-reduction recost artifact,
- the latest quality-aware HBM-controller-PPA integrated frontier artifact,
- the successful one-group full GQA8 equivalence evidence,
- the successful four-group full GQA8 rotation equivalence evidence.

The audit must replace the obsolete reduction latency term without
double-counting, preserve throughput/energy/area/precision reporting, and fail
closed when any prerequisite is missing, failed, or contract-mismatched.
