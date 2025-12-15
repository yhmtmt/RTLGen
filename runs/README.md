Purpose
-------
- Track evaluated RTLGen configurations in a lightweight, repo-visible way (configs, generated Verilog, and CSV metrics only).
- Provide a queue for unevaluated configs: add a JSON config here to invite others to run it and append metrics.

Layout
------
- `runs/<circuit_type>/<design>/config.json` — the config that produced the metrics (e.g., `runs/prefix_adders/adder_ripple_4u_wrapper/config.json`).
- `runs/<circuit_type>/<design>/verilog/*.v` — generated RTL for that config (no DEF/GDS/logs).
- `runs/<circuit_type>/<design>/metrics.csv` — aggregated execution parameters and parsed metrics per run; new sweeps append rows.
- `runs/<circuit_type>/<design>/work/` — transient per-run scratch (may be cleared without losing the published artifacts).

Contribute
----------
- Add a new config under `runs/<circuit>/config.json` (or a variant name) and open a PR; keep configs minimal and documented.
- Run `scripts/run_sweep.py ... --out_root runs` locally; it will append rows to `metrics.csv` and refresh `verilog/`.
- If you can’t run flows, still contribute literature context: add brief design notes and paper links in `plan/log.md` or include a `README.md` beside the config summarizing the idea, target metrics, and references.
- Do not check in large binaries (logs/DEF/GDS); keep this directory light to encourage frequent evaluation by others/agents.
