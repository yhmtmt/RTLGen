RTLGen End-to-End Workflow (Design -> PPA -> Model -> Feedback)
================================================================

Goals
-----
- Make it fast to find the right RTL design in `runs/` by name, tags, or PPA.
- Enable distributed evaluators to add results without stepping on each other.
- Keep results reproducible: record config, tool versions, and flow knobs.
- Feed PPA data back into the auto-generation algorithm and the RTL model.

Workflow Stages
---------------
1) Design intent
   - Inputs: JSON config (RTLGen) or external RTL (handwritten/Yosys/other).
   - Output: a design directory under `runs/designs/<circuit_type>/<design>/` with metadata.

2) RTL generation (auto or external)
   - RTLGen: `scripts/generate_design.py` creates `verilog/` from `config.json`.
   - External: include `verilog/` (or `source/`) plus a short `README.md` with origin.

3) Evaluation (OpenROAD flow)
   - Use `scripts/run_sweep.py` or a dedicated evaluator.
   - Append rows to `metrics.csv` in the design directory.

4) Aggregation / indexing
   - Generate a global `runs/index.csv` from all `metrics.csv` files.
   - Provide a minimal search UI or web service over this index.

5) Learning + feedback
   - Train/update PPA prediction model from `runs/index.csv`.
   - Feed predicted PPA back into RTLGen search/ILP to prune or bias candidates.

Runs Directory Data Model
-------------------------
Directory layout (proposed additions marked with "*"):
- `runs/designs/<circuit_type>/<design>/`
  - `config.json` (RTLGen configs) or `source.md`* (external RTL design notes)
  - `verilog/` (generated or imported RTL)
  - `metrics.csv` (append-only: one row per evaluation run)
  - `metadata.json`* (machine-readable summary)
  - `README.md`* (short human summary, links to papers, rationale)
  - `work/` (scratch; excluded from indexing)
- `runs/campaigns/<circuit_type>/<campaign>/`
  - `configs/` (input configs used to generate designs)
  - `sweeps/` (OpenROAD sweep definitions)
  - `*_summary.csv` and `best_*.csv` (aggregated results)

Suggested `metadata.json` fields:
- `design_id`, `circuit_type`, `generator` (rtlgen/yosys/manual/other)
- `ops` (e.g., multiplier/adder), `widths`, `signedness`
- `rtl_source` (script version or commit hash), `owner`, `tags`
- `created_at`, `notes`

Suggested `metrics.csv` columns (extend as needed):
- `run_id` (unique), `git_commit`, `pdk`, `clock_ns`, `util`, `place_density`
- `area_um2`, `power_mw`, `tns`, `wns`, `crit_ns`, `status`
- `flow_id`, `openroad_rev`, `flow_args`, `toolchain` (optional)

Distributed Evaluators and Consistent Merging
---------------------------------------------
Current workflow relies on human-organized git merges. A lightweight automation
layer can help evaluators work independently while keeping results consistent.

Proposed evaluator behavior:
- Watch `runs/designs/` for new `config.json` or `source.md` entries.
- Run OpenROAD evaluation locally.
- Append to `metrics.csv` and open a PR.

Consistency rules:
- `metrics.csv` is append-only.
- Each evaluation generates a stable `run_id` (hash of config + flow knobs).
- CI checks for duplicate `run_id` or schema drift.
- CI regenerates `runs/index.csv` and ensures it is committed.

Automation options:
- Local: `scripts/watch_runs.py` to detect new designs and queue evaluations.
- CI: GitHub Actions job to rebuild the index and validate schema.
- Bot: simple GitHub App to auto-open PRs from evaluator workers.

Finding Designs Quickly (Search + Web Service)
----------------------------------------------
A fast search layer makes `runs/` usable for humans and bots.

Baseline approach:
- Build `runs/index.csv` (or `runs/index.parquet`) from all `metrics.csv` files.
- Add a tiny static web app (HTML+JS) that loads the index and supports:
  - Filters: `circuit_type`, `width`, `signedness`, `generator`, `pdk`
  - Sort by area/delay/power
  - Links back to `runs/designs/<circuit>/<design>/`

Possible architecture:
- Static: `scripts/build_runs_index.py` + `docs/runs/index.html`.
- API: a small Flask/FastAPI service that reads `runs/index.csv`.

Ingestion of Non-RTLGen Designs
-------------------------------
To include external RTL:
- Put the RTL under `runs/designs/<circuit_type>/<design>/verilog/`.
- Add `source.md` describing origin, assumptions, and license.
- Provide a minimal `metadata.json` (generator="manual" or "yosys").
- The evaluator treats it like any other design and appends `metrics.csv`.

Training Loop (PPA Model)
-------------------------
- Dataset: `runs/index.csv` + derived features (widths, op count, CPA/PPG type).
- Model output: predicted PPA (area/delay/power) + uncertainty.
- RTLGen feedback:
  - Use predictions to prune candidate search early.
  - Use predictions to seed ILP objective weights or choose CPA/PPG.
  - Target: reduce evaluation churn while keeping accuracy.

Near-Term Implementation Plan
-----------------------------
- Add `metadata.json` spec and validation script.
- Add `scripts/build_runs_index.py` to aggregate `metrics.csv` into index.
- Add a simple static web page under `docs/runs/` to filter/search.
- Add CI job to validate and regenerate the index on PRs that touch `runs/`.
