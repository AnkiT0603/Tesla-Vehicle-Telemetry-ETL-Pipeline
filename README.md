# Tesla Vehicle Telemetry ETL Pipeline

Major data engineering project for processing Tesla-style connected vehicle telemetry from Amazon S3, orchestrating ETL with Apache Airflow, and loading curated near-real-time monitoring tables into Snowflake.

## Project Scope

This project is designed as a portfolio-grade, end-to-end ETL system. It covers ingestion, schema validation, data quality checks, transformations, warehouse loading, orchestration, observability, and deployment-ready configuration.

## Architecture

```mermaid
flowchart LR
    A["Tesla Vehicle Telemetry Producers"] --> B["Amazon S3 Raw Zone"]
    B --> C["Airflow DAG"]
    C --> D["Python ETL Package"]
    D --> E["Validated Parquet Files"]
    E --> F["Snowflake Internal Stage"]
    F --> G["Snowflake Staging Tables"]
    G --> H["Curated Monitoring Tables"]
    H --> I["Near-Real-Time Monitoring Dashboards"]
    C --> J["Processed S3 Object Control Table"]
```

## Features

- S3 raw telemetry ingestion with partition-aware paths.
- Incremental object processing using a Snowflake `PROCESSED_S3_OBJECTS` control table.
- Schema enforcement for vehicle telemetry events.
- Data quality rules for battery, speed, location, odometer, timestamp, duplicate events, and VIN fields.
- Transformations for trip metrics, battery health, alerts, and monitoring aggregates.
- Snowflake stage, staging tables, `COPY INTO`, and `MERGE` based curated loading.
- Airflow DAG with extract, validate, transform, load, and quality-gate tasks.
- Local sample data and tests for fast development.
- Environment-based configuration for AWS, Snowflake, and Airflow.
- GitHub Actions workflow for automated tests.

## Repository Structure

```text
.
|-- .github/workflows/ci.yml
|-- dags/
|   `-- tesla_telemetry_etl_dag.py
|-- data/
|   `-- sample/
|       `-- tesla_telemetry_sample.jsonl
|-- docs/
|   |-- architecture.md
|   `-- data_dictionary.md
|-- snowflake/
|   |-- 001_create_database_schema.sql
|   |-- 002_create_tables.sql
|   `-- 003_curated_models.sql
|-- src/
|   `-- telemetry_etl/
|       |-- config.py
|       |-- extract.py
|       |-- load.py
|       |-- quality.py
|       |-- schemas.py
|       `-- transform.py
|-- tests/
|   |-- test_quality.py
|   `-- test_transform.py
|-- docker-compose.yml
|-- pyproject.toml
|-- requirements.txt
`-- .env.example
```

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -e ".[dev]"
```

3. Run tests:

```bash
pytest
```

4. Run the local ETL sample:

```bash
python -m telemetry_etl.transform data/sample/tesla_telemetry_sample.jsonl build/curated
```

On Windows PowerShell:

```powershell
.\scripts\run_local_etl.ps1
```

5. Start Airflow locally:

```bash
docker compose up airflow-init
docker compose up
```

Airflow UI will be available at `http://localhost:8080` with username `airflow` and password `airflow`.

## Sample Output

Running the local ETL sample creates curated Parquet files in `build/curated`:

- `telemetry_enriched.parquet`
- `vehicle_hourly_metrics.parquet`

## Snowflake Setup

Run the SQL files in order:

```text
snowflake/001_create_database_schema.sql
snowflake/002_create_tables.sql
snowflake/003_curated_models.sql
```

The Airflow DAG uploads curated Parquet files to `TELEMETRY_INTERNAL_STAGE`, copies them into staging tables, merges them into curated tables, and records processed S3 keys after a successful load.

## Environment Variables

Copy `.env.example` to `.env` and fill in values for AWS, Snowflake, and Airflow.

## Major Project Evaluation Points

This project qualifies as a major data engineering project because it includes:

- Cloud object storage ingestion.
- Workflow orchestration.
- Warehouse modeling.
- Data validation and quality gates.
- Incremental loading and processed-file tracking.
- Snowflake staging, copy, and merge loading.
- Modular Python package.
- Test coverage and CI.
- Deployment-ready local Airflow environment.
- Documentation for architecture, schemas, and operations.

