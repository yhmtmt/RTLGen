# Design Brief

- `proposal_id`: `prop_cp_artifact_sync_submission_progress_v1`
- scope: control-plane workflow validation
- target behavior: artifact-sync resolver should not open a blocked-submission case when recent run events already show review publication, submission preparation, PR creation, or completion processing without a newer submission failure.

## Direction Gate

- status: approved
- approved_by: operator
- approved_utc: 2026-04-28T08:50:00Z
- note: Run one fresh normal workflow item after PR #240 and confirm resolver quietness.
