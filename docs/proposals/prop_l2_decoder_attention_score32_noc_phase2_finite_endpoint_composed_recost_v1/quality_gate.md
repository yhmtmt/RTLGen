# Quality Gate

- Consume only the exact three merged dependencies named by the proposal.
- Require complete finite-endpoint RTL/performance counter equivalence.
- Rerun release conversion, mesh routing, and finite endpoint service at the conservative composed clock.
- Derive token latency from the slower of compute-layer time and finite NoC drain time.
- Replace prior router, FIFO, and endpoint PPA; do not add aggregate PPA on top.
- Inherit the arithmetic precision and quality evidence without claiming a new quality run.
- Keep scheduler PPA, SRAM physical/energy closure, activity power, and HBM/DRAM explicit.
- Materialize attention-head, KV-head, and GQA structure; do not label GQA8 as exact Llama-2-7B.
