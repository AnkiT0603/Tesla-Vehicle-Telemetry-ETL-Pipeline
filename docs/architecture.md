[architecture.md](https://github.com/user-attachments/files/28380696/architecture.md)
# Architecture

## Objective

The pipeline turns raw connected vehicle telemetry into warehouse-ready tables for monitoring dashboards and alerting.

## Layers

1. Raw zone: JSON Lines telemetry lands in Amazon S3 using date/hour partitions.
2. Orchestration: Airflow discovers new raw objects, downloads them to a landing area, validates records, transforms them, and stages curated Parquet files.
3. Processing: Python modules apply schema validation, quality checks, enrichment, and hourly aggregation.
4. Warehouse: Snowflake stores raw, enriched, and aggregate monitoring data.
5. Serving: Snowflake views expose near-real-time vehicle status and alerts.

## Incremental Strategy

The DAG runs hourly and processes only S3 objects that have not yet been registered in the Snowflake `PROCESSED_S3_OBJECTS` control table. Processed keys are written only after curated tables are successfully loaded.

## Reliability

- Airflow retries transient S3 and Snowflake failures.
- Quality gates fail the DAG before bad data reaches curated tables.
- Pydantic validates event shape and allowed categorical values.
- Snowflake SQL is split into database, table, and view layers.
- Curated Parquet files are copied into Snowflake staging tables and merged into final tables using business keys.

## Suggested Dashboard KPIs

- Active vehicles by model.
- Average battery percentage by hour.
- Low battery vehicles.
- Tire pressure alerts.
- High speed events.
- Last known location by VIN.
- Charging vs driving distribution.
