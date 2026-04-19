LLM Decoder Tiny v1
===================

Purpose
-------
Reference-only model contract for the first decoder-quality stage.

Current status
--------------
Placeholder contract only.

What exists now:
- `model_contract.json`

What does not exist yet:
- trained weights
- tokenizer-faithful model export
- runnable mapper lowering
- real decoder inference path

This contract exists so dataset artifacts can bind to a specific model identity
and reference-output schema without pretending a real small decoder is already
integrated into the repository.
