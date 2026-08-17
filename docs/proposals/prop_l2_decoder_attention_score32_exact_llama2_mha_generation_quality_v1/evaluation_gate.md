# Evaluation Gate

- The requested model ID is exactly `meta-llama/Llama-2-7b-hf`.
- Hidden size is 4096.
- Attention-head count is 32.
- KV-head count is 32.
- GQA group size is 1 (MHA).
- The primary candidate is `score32_exp_lut_div`.
- Teacher-forced mean NLL delta is at most 0.4.
- Candidate mean probability on the reference token is at least 0.1.
- Free-running token match rate is at least 0.75.

Missing checkpoint authorization fails the job prerequisite and must not be interpreted as a quality hold.
