# Quality Gate

Run:

```sh
python3 -m pytest -q \
  tests/test_noc_sram_packet_mesh_perf.py \
  tests/test_llm_decoder_attention_score32_noc_phase2_endpoint_rtl.py \
  tests/test_llm_decoder_attention_score32_noc_phase2_schedule.py
```

Also require the focused L2 generator test, result-consumer tests, run
validation, and `git diff --check`. The remote command must remain bounded and
must not emit per-flit traces as declared artifacts.
