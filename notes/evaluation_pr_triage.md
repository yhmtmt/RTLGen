Evaluation PR Triage Checklist
==============================

Purpose
-------
Use this when reviewing evaluator-submitted PRs (especially queue/OpenROAD
results) so merge/close decisions stay consistent after contract updates.

Scope
-----
- PRs that modify `runs/` artifacts, queue items, or Layer2 campaign outputs.
- Maintainer-side triage, not evaluator execution instructions.

Quick Decision Flow
-------------------
1. Identify overlap/supersession:
   - Is there a newer rerun PR for the same queue item and benchmark set?
2. Check contract compliance:
   - Campaign rows must carry benchmark provenance:
     `model_set_id`, `model_manifest`, `onnx_sha256`.
   - Prefer hashes when available:
     `mapper_arch_hash`, `perf_config_hash`.
3. Run required validation on the PR branch:
   - `python3 scripts/validate_runs.py`
   - If campaign JSON changed:
     `python3 npu/eval/validate.py --campaign <campaign.json> --check_paths`
4. Decide:
   - Merge: compliant and currently best/needed sample set.
   - Close as superseded: older PR replaced by newer rerun PR.
   - Request rerun from latest `master`: missing required contract fields.

Label Policy (current repo labels)
----------------------------------
- `question`: needs rerun or clarification before merge.
- `duplicate`: superseded by a newer PR covering the same item.
- `invalid`: artifacts violate required schema/validation and are not usable.

Review Checklist
----------------
- [ ] Queue item state transition is correct (`queued` -> `evaluated`) when applicable.
- [ ] `metrics_rows` references point to real rows.
- [ ] `results.csv` and result-row JSON are consistent and append-only.
- [ ] Provenance fields are present and coherent with campaign/model manifest.
- [ ] Validation commands pass.
- [ ] No heavy temporary artifacts (DEF/GDS/log dumps).

Comment Templates
-----------------
Superseded PR:
```
Thanks for the run. This PR is superseded by a newer rerun for the same item.
To keep one canonical branch of record, we are closing this as duplicate and
continuing on PR #<newer_pr>.
```

Needs rerun on latest contract:
```
Thanks for the run. We cannot merge this as-is because campaign/result artifacts
do not match the current evaluation contract (benchmark provenance fields are
required: model_set_id/model_manifest/onnx_sha256). Please rerun from latest
master and resubmit.
```
