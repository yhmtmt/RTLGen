# Design Brief

The prior attention/KV memory reports were analytical. PR #478 added measured
Layer 1 PPA for six standalone `attention_kv_tile` frontier points, and PR #480
made the Layer 2 estimator able to ingest those metrics.

This job reruns the attention/KV memory report with the measured tile metrics
explicitly attached. It should not be read as a full integrated decoder
measurement. The purpose is to decide whether standalone datapath cost changes
the next priority, or whether the frontier still requires producer, memory
hierarchy, and NoC coupling.

The expected next step after this refresh is a bounded producer/memory/NoC
coupled attention job if the measured tile evidence does not invalidate that
direction.
