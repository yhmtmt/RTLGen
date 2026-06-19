# Quality Gate

The proposal does not itself judge KV4. It consumes the 7B native quality gate
and keeps the first physical-HBM rerank conservative at KV16/KV8. If the 7B gate
shows KV4 is safe, open a separate KV4-inclusive rerank or recovery proposal.
