# Quality Gate

- status: pending
- required:
  - `tests/test_attention_kv_reducer_folded.sh` passes.
  - Dry-run sweep covers producer-coupled p8/p16 and ppc2/ppc4 points.
  - Remote PPA records both ok and failed rows as boundary evidence.
  - Result interpretation compares standalone boundary, internal-source, and producer-coupled metrics separately.
