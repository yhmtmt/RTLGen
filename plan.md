# RTLGen Repository Improvement Plan (2026)

## Purpose
This document is the forward-looking roadmap for improving the RTLGen
repository as a two-layer optimization workspace:

- **Layer 1**: circuit module generation + physical optimization
  (`docs/layer1_circuit_workflow.md`).
- **Layer 2**: NPU architecture exploration on real ONNX workloads
  (`npu/docs/workflow.md`).

It complements (does not replace):
- `plan/log.md` (append-only execution history)
- `docs/structure.md` (documentation roles and canonical precedence)

## Current Snapshot (as of 2026-03)
### What is already strong
- Clear doc-role boundaries and canonical runbooks:
  `docs/structure.md`, `docs/two_layer_workflow.md`, `docs/layer1_circuit_workflow.md`,
  `npu/docs/index.md`, `npu/docs/workflow.md`, `npu/docs/status.md`.
- Layer 2 campaign infrastructure with validation, reporting, objective sweeps:
  `npu/eval/*`, `runs/campaigns/npu/*`.
- Shell/mapper/sim foundations:
  `npu/shell/spec.md`, `npu/mapper/*`, `npu/sim/*`, golden regressions and CI.
- Distributed evaluation queue model with traceability rules:
  `runs/eval_queue/*` and `notes/evaluation_agent_guidance.md`.

### Where friction still exists
- Some authored notes are now out of date vs the current NPU implementation
  (e.g. early “requirements” and legacy build paths).
- “Next steps” sections in multiple NPU docs can drift from the execution log.
- Long-range architecture-search notes are still aspirational and need to stay
  anchored to the existing campaign/result-row contract.
- There is no single, compact “roadmap” document (this file should become that).

## Guiding Principles
1. **Keep contracts explicit and file-based.** Avoid hidden coupling between layers.
2. **Append-only results with validation gates.** Never rewrite `runs/**` history.
3. **Feature gates for algorithm changes.** New generators stay behind config
   switches until validated (see `notes/development_agent_guidance.md`).
4. **Prefer small, reproducible increments.** Every milestone should leave the
   repo in a runnable state with CI coverage.

## Roadmap
### P0 — Documentation Hygiene and Navigation (1–2 weeks)
Goals: reduce confusion, make “what to read / what to run” unambiguous.

- [ ] Create a short “Getting Started by Layer” page and keep it aligned with
      `README.md` and canonical runbooks.
- [ ] Audit and update outdated authored notes:
  - `notes/rtlgen_npu_requirements.md`: mark historical assumptions and update
    the “current repo status” section to reflect the implemented Layer 2 flow.
  - `notes/constant_multiplication.md`: align build/run instructions with the
    current CMake targets and OR-Tools discovery policy.
- [ ] Sync NPU doc “Next steps” sections with the actual status:
  - Remove items that are already implemented (e.g. phase-1 mapper split),
    and replace with the next concrete blockers.
- [ ] Add a lightweight “doc freshness” checklist to `plan/log.md` cadence:
  update `npu/docs/status.md` and any affected plan docs after each sweep milestone.

Definition of done:
- A new contributor can find the right runbook in <5 minutes and can run
  (a) a Layer 1 smoke gen, and (b) a Layer 2 baseline campaign without guessing.

### P1 — Developer Experience and CI Hardening (1–3 weeks)
Goals: make local checks consistent with CI, and keep breakages shallow.

- [ ] Add a single “repo check” entrypoint (extend the existing Makefile or add
      one script), e.g.:
  - C++: configure + build + a minimal `ctest` profile
  - Python: mapper/eval/synth regression tests
  - Data: `python3 scripts/validate_runs.py` + `python3 scripts/build_runs_index.py`
- [ ] Extend CI to run a minimal `ctest` profile (not only python/NPU tests)
      with minimal deps:
  - reuse the OR-Tools + ONNX Runtime install already present in
    `npu-golden-sim.yml`
  - keep FloPoCo-dependent FP tests in a separate extended profile/job instead
    of making every CTest job carry the full dependency set
- [ ] Ensure devcontainer usage on Apple Silicon is explicit:
  - keep `linux/amd64` policy consistent across devcontainer docs/files
  - add a short performance note + expected build time ranges

Definition of done:
- Any PR that breaks build/tests is caught by CI without requiring OpenROAD.

### P2 — Layer 1: Module Algorithm and Evaluation Improvements (parallel track)
Goals: make module-level advances feed the NPU layer with better primitives.

Multiplier/compressor tree track (from `notes/compressor_tree/memo_about_compressor_tree.md`):
- [ ] Fix/unstick the **direct compressor-assignment ILP** for ≥16-bit.
- [ ] Define and document how 4:2 compressors are modeled for timing (current
      4:2-as-two-3:2 caveat can mislead stage-count objectives).
- [ ] Re-run and label multiplier baselines carefully (pre-change vs post-change),
      and publish updated comparative summaries under `runs/`.

Pipeline/architecture knobs:
- [ ] Extend configs to support pipeline placement depth beyond “fixed to 1”
      where it materially improves PPA (with validation gates and defaults).
- [ ] Add a first-class MAC generator path (dot product / accumulate) and
      evaluate it under the Layer 1 workflow.

Definition of done:
- A per-PDK “module candidates” manifest exists for at least the NPU’s key
  compute blocks, with clear `wrapped_io` vs `macro_hardened` scope.

### P3 — Layer 2: NPU v0.2 Hardening and Scale-Out (2–8 weeks)
Goals: move from smoke/practical MLPs to broader ONNX workloads with stable contracts.

Architecture spec and validation:
- [ ] Review and freeze `arch v0.2` required fields (`npu/docs/arch_v0_2_draft.md`).
- [ ] Implement deeper schema validation (types/ranges/enums) and surface clear errors.
- [ ] Consume interconnect/mapping constraints in downstream mapper/perf policy,
      not only in docs.

Mapper/general tiling:
- [ ] Generalize beyond the current phase-1 MLP `GEMM2` N-axis chunking:
  - support additional split axes (M/K) and/or multi-layer chains
  - extend split policy beyond the current MLP lowering path to additional
    patterns that hit SRAM-fit failures
  - produce explicit split provenance in schedule + campaign row notes
- [ ] Add a small suite of “intentional overflow” models that must map via tiling.

Simulation fidelity:
- [ ] Improve perf memory modeling (burst/outstanding/latency) and keep the
      assumptions synchronized with `npu/sim/perf/README.md`.
- [ ] Expand constrained-random parity coverage for vector derivatives and fp16
      edge behavior (as tracked in `npu/docs/sim_dev_plan.md`).

Physical integration:
- [ ] Implement sky130hd SRAM macro generation and hook it into synthesis
      (current policy is memgen-first with CACTI fallback; see
      `npu/docs/workflow.md`).
- [ ] Add compute-enabled (non-fp16-backend) block sweep runbooks and targets,
      so DMA/CQ + GEMM/VEC variants are physically comparable.

Definition of done:
- A campaign can run end-to-end on the supported practical ONNX model set with:
  - stable contract validation,
  - mapping that does not fail solely due to SRAM fit for supported models
    (tiling or an explicit split policy kicks in),
  - merged rows that include physical + perf metrics and provenance.

### P4 — Architecture Search and “Scaling Laws” Research (long-term)
The `plan/chat_with_chatgpt5.3/*` notes describe the long-term direction:
architecture search + discovery of scaling relations under physical constraints.

Near-term steps that make this research operational:
- [ ] Add explicit **compute-vs-communication diagnostics** to campaign reports:
  - roofline-style summaries (bytes moved vs ops)
  - per-op stall breakdowns
  - simple “Rent-like” connectivity proxies from generated topology
- [ ] Define a small set of **architecture templates** (tile/memory/fabric) with
  a consistent parameter surface and tie them to:
  - generation (`npu/arch/to_rtlgen.py`)
  - mapping legality checks
  - reporting dimensions
- [ ] Add a “search harness” wrapper (even if initially grid/random search)
      on top of the existing campaign contract, not as a parallel artifact
      format:
  - emit standard `campaign.json` / `results.csv` outputs under
    `runs/campaigns/npu/`
  - candidate generation policy
  - constraints violated
  - objective profiles used
  - best-point stability across reruns

Definition of done:
- Architecture points can be compared with both (a) PPA/perf outcomes and (b)
  explanatory scaling diagnostics that help propose new design rules, while
  staying inside the canonical campaign/result-row ledger.

## Risks / Watch Items
- **Apple Silicon devcontainer performance**: amd64 emulation is slower; keep
  “fast path” scripts available for python-only Layer 2 work outside OpenROAD.
- **Doc drift**: keep `status.md` and “Next steps” synced after each sweep.
- **Over-optimization early**: resist adding complex search methods before the
  contract + mapping + reporting loop is stable.
