.PHONY: install test local-transform

install:
	pip install -e ".[dev]"

test:
	pytest

local-transform:
	python -m telemetry_etl.transform data/sample/tesla_telemetry_sample.jsonl build/curated

