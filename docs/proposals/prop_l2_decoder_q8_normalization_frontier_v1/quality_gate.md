# Quality Gate

A q8 reciprocal-normalization row may become the next implementation candidate only if it has:

- 24/24 next-token matches on the prompt-stress dataset
- 24/24 top-k containment on the prompt-stress dataset

Rows that preserve only top-k containment remain diagnostic and should not replace the exact-safe anchor.
