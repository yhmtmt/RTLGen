Runs Dataset Sets
=================

Purpose
-------
Shared prompt/data slices for model-quality and decoder-accuracy evaluation.

Contract
--------
Each dataset set lives under `runs/datasets/<dataset_id>/` and should provide a
`manifest.json` with:
- `version`
- `dataset_id`
- `task`
- `sample_file`
- `sample_count`
- optional tokenizer/model/reference metadata

Current sets
------------
- `llm_decoder_eval_tiny_v1`: tiny curated prompt set for the first decoder
  quality-gate stage. This is a placeholder inference-evaluation dataset, not a
  training corpus.
