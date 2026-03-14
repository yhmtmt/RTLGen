# Phase 2 Real Ingestion Status

Archive note:
- historical status note recording when real ingestion became proven
- not a routine operator manual

Status: proven

Scope proven on real repo-facing items:
- Layer 1 DB-native generation -> worker -> result consumer -> review package -> submission PR
- Layer 2 DB-native generation -> worker -> result consumer -> review package -> submission PR

Merged evidence:
- Layer 1 ingestion PR: `#16`
  - merge commit: `23c5be1`
  - item: `l1_real_softmax_r4_shift5_submit_v1`
- Layer 2 ingestion PR: `#17`
  - merge commit: `682d421`
  - item: `l2_real_softmax_submit_v1`

What is now established:
- PostgreSQL-backed control-plane execution works for real OpenROAD-facing runs
- DB-native generator/consumer paths work for both `l1_sweep` and `l2_campaign`
- review packages are sufficient to drive real GitHub draft PR submission
- submission reruns correctly reuse the existing PR branch
- submitted queue snapshots keep repo-portable metric references

Current baseline:
- operator entrypoint: [phase2_baseline.md](/workspaces/RTLGen/control_plane/phase2_baseline.md)
- practical workflow: generate work in DB, run worker, consume result, then `operate-submission`

Remaining work is productization, not feasibility:
- eligibility policy for one-shot submission
- long-running remote worker/server deployment
- operator/reporting polish
