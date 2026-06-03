# Reference Paper Intake

Use this directory for papers needed to seed or audit the design evidence
registry under `runs/design_registry/`.

## Workflow

If a paper or datasheet cannot be retrieved from public internet sources, add a
record to `missing_papers.jsonl`. After obtaining the PDF through an appropriate
library or institutional channel, place it in this directory and update the
record with `local_pdf`.

Large PDFs should normally remain local working-copy inputs unless the project
explicitly decides to track them. The registry should cite the canonical public
URL when available and may also cite `local_pdf` for extraction provenance.

## Missing Paper Record

Each line in `missing_papers.jsonl` is a JSON object:

```json
{
  "paper_id": "short_stable_id",
  "title": "Paper title",
  "authors": ["Author One", "Author Two"],
  "venue_year": "Conference 2026",
  "canonical_url": "https://example.org/paper",
  "reason_unavailable": "paywalled_or_blocked",
  "needed_for": "runs/design_registry external measurement seed",
  "local_pdf": "",
  "notes": ""
}
```

## Extraction Target

When a PDF is available, extract only the data needed for comparison:

- technology node and voltage,
- clock frequency,
- precision and operation counting convention,
- MACs/cycle or TOPS/OPS with conversion rule,
- area and area scope,
- power and workload,
- SRAM/cache/memory hierarchy included in the reported area,
- whether the result is measured silicon, post-layout, post-synthesis, or
  simulation.

