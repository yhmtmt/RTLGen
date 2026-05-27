# Evaluation Gate

Required inputs:

- merged corrected compute frontier for nm1..nm64,
- merged iso-utilization check for nm32/nm64,
- merged quality-backed Llama7B physical-HBM memory/NoC frontier.

The evaluation must not promote KV4 or MQA as deployable candidates. It may report them only in separate lower-bound work, which is out of scope here.

