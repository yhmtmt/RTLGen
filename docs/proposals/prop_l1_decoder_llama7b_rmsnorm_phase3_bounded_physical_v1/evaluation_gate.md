# Evaluation Gate

- status: approved
- approved_by: developer_agent
- approved_utc: 2026-08-10T00:00:00Z
- allowed_evaluations:
  - generate the LANES=16 Phase-3 RTL from the checked config
  - run the physical contract guard and Verilator lint
  - run the bounded Nangate45 OpenROAD sweep defined in the proposal
  - extract `timing_debug_report.md`
- note: Do not run OpenROAD locally and do not insert a DB item from this branch.

