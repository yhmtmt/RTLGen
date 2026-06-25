# Llama7B Mixed/Int8 Score Margin Audit

This proposal adds a cheap evidence-only audit after the score precision recovery sweep. It consumes the merged recovery JSON, buckets top1 misses by reference margin, and decides whether the remaining drift is narrow-margin/top-k-stable or systematic.

No new PPA or model inference is requested by this job.
