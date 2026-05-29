$ErrorActionPreference = "Stop"

python -m telemetry_etl.transform data/sample/tesla_telemetry_sample.jsonl build/curated

Write-Host "Local ETL completed. Curated files are in build/curated."

