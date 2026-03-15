# Developer Loop Workspace

This directory is the notebook-side working area for developer-agent proposal
artifacts.

Use it for:
- one subdirectory per active proposal
- approval-gate records
- local analysis artifacts that support notebook-side autonomous iteration

Recommended layout:
```text
docs/developer_loop/
  README.md
  _template/
  <proposal_id>/
```

Rules:
- keep one proposal directory per active direction
- keep artifacts notebook-local until the direction is promotion-worthy
- do not use this directory for evaluator execution products
- use the control plane only for deterministic remote evaluation, not for these notebook-side artifacts

Start from:
- `_template/`

Canonical design docs:
- `docs/developer_agent_loop.md`
- `docs/developer_agent_artifacts.md`
- `docs/developer_agent_orchestration.md`
