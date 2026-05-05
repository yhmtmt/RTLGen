# Design Brief

The measured merge/FIFO result showed flat rank remains the compute-latency winner. The unresolved question is whether streaming remains useful as a memory-traffic hierarchy.

This job reruns the existing overlap sweep with:

- measured rank datapath PPA
- measured candidate merge/FIFO PPA
- explicit memory bandwidth and energy planning parameters
- NoC hop energy planning parameters

The result should report separate recommendations for compute latency, overlap recovery, and memory traffic.
