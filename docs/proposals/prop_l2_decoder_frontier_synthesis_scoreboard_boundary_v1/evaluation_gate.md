# Evaluation Gate

Accept the job if it:

- reruns stage breakdown, attention/KV memory, producer/ranker coupling, and frontier synthesis
- includes `producer_control_boundary` in the producer/ranker JSON
- reports the SOFTMAX/EVENT guard decision and synth status in the frontier markdown
- keeps the previous frontier synthesis result as the paired baseline
- keeps generated artifact paths repo-portable
