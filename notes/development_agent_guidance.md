Development Agent Guidance
==========================

Purpose
-------
This document defines how developer agents should introduce new circuit
generation algorithms while protecting existing baselines and evaluation
traceability.

Branching Policy
----------------
When starting work on a new algorithm or a significant behavior change:
- Create a dedicated branch before making changes.
- Keep experimental work isolated until evaluation is complete.
- Request a pull to `master` only after the evaluation criteria are satisfied.

Configuration Switches
----------------------
New algorithms must be gated behind an explicit configuration switch:
- Do not overwrite or silently replace the legacy algorithm.
- The legacy path must remain the default until the new path is validated.
- The configuration option should be documented in `examples/about_config.md`.

Validation Requirements
-----------------------
Before requesting a pull to `master`, developers must:
- Test the algorithm across relevant parameter settings (widths, signedness,
  PPG/CPA choices, or other algorithm-specific knobs).
- Document the feasible parameter range that was validated (e.g., width limits,
  supported compressor libraries).
- Call out known limitations or failure cases.

Evaluation Discipline
---------------------
Follow `notes/evaluation_agent_guidance.md` for evaluation structure, and:
- Create new, distinctive design and campaign directories under `runs/` for
  each new algorithm or configuration switch.
- Keep evaluation artifacts traceable to the algorithm version and config.

Merge Criteria
--------------
Do not replace the legacy algorithm until evaluation shows the new algorithm is
valid and at least non-regressing in target metrics. If results are mixed or
inconclusive, keep the legacy path as default and continue evaluation.
