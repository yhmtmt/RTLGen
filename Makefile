.PHONY: runs-index runs-validate runs-refresh

runs-index:
	python scripts/build_runs_index.py

runs-validate:
	python scripts/validate_runs.py

runs-refresh: runs-index runs-validate
