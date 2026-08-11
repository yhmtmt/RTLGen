# Quality Gate

- Exact canonical dependency identities are required.
- Both reroutes must remain workload-complete with eight waves, 128 tiles, and
  every scheduled flit delivered.
- The output must state that the old absolute 1 ns timeline was not reused.
- The primitive-clock case cannot be promoted as aggregate mesh clock closure.
- Run
  `python3 -m pytest -q tests/test_reroute_llm_decoder_attention_score32_noc_phase2_measured_router_clock.py`.
