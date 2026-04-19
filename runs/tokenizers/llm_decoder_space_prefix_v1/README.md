LLM Decoder Space Prefix v1
===========================

Purpose
-------
Deterministic placeholder tokenizer for the first decoder-quality stage.

Behavior
--------
- split text into runs of non-space characters
- attach any immediately preceding spaces to the token
- preserve punctuation as part of the token text

Examples
--------
- `The capital of France is` -> `["The", " capital", " of", " France", " is"]`
- ` Paris` -> `[" Paris"]`
- `2 + 2 =` -> `["2", " +", " 2", " ="]`

Limits
------
- not model-faithful
- no unknown-token fallback
- intended only for early decoder-quality scaffolding

This tokenizer exists to make the tiny decoder dataset produce one deterministic
next token per sample without pretending a real LLM tokenizer is already wired.
