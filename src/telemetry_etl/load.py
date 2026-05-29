from pathlib import Path
import re

import snowflake.connector

from telemetry_etl.config import Settings, get_settings

SNOWFLAKE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def snowflake_connection(settings: Settings | None = None):
    cfg = settings or get_settings()
    return snowflake.connector.connect(
        account=cfg.snowflake_account,
        user=cfg.snowflake_user,
        password=cfg.snowflake_password,
        role=cfg.snowflake_role,
        warehouse=cfg.snowflake_warehouse,
        database=cfg.snowflake_database,
        schema=cfg.snowflake_schema,
    )


def execute_sql_file(path: str | Path, settings: Settings | None = None) -> None:
    sql = Path(path).read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)


def put_parquet_to_stage(
    local_path: str | Path,
    stage_name: str,
    settings: Settings | None = None,
    stage_prefix: str | None = None,
) -> str:
    file_path = Path(local_path).resolve()
    stage_ref = _stage_reference(stage_name, stage_prefix)
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(f"PUT file://{file_path.as_posix()} {stage_ref} AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
    return f"{stage_ref}/{file_path.name}"


def copy_parquet_from_stage(
    table_name: str,
    stage_name: str,
    stage_prefix: str,
    file_pattern: str,
    settings: Settings | None = None,
) -> None:
    table = _identifier(table_name)
    stage_ref = _stage_reference(stage_name, stage_prefix)
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                COPY INTO {table}
                FROM {stage_ref}
                FILE_FORMAT = (TYPE = PARQUET USE_VECTORIZED_SCANNER = TRUE)
                MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
                PATTERN = '{file_pattern}'
                ON_ERROR = 'ABORT_STATEMENT'
                """
            )


def merge_stage_table(target_table: str, source_table: str, key_columns: list[str], settings: Settings | None = None) -> None:
    target = _identifier(target_table)
    source = _identifier(source_table)
    keys = [_identifier(column) for column in key_columns]
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            columns = _table_columns(cur, target)
            non_key_columns = [column for column in columns if column not in set(keys)]
            update_clause = ", ".join(f"target.{column} = source.{column}" for column in non_key_columns)
            insert_columns = ", ".join(columns)
            insert_values = ", ".join(f"source.{column}" for column in columns)
            join_clause = " AND ".join(f"target.{column} = source.{column}" for column in keys)
            cur.execute(
                f"""
                MERGE INTO {target} AS target
                USING {source} AS source
                ON {join_clause}
                WHEN MATCHED THEN UPDATE SET {update_clause}
                WHEN NOT MATCHED THEN INSERT ({insert_columns})
                VALUES ({insert_values})
                """
            )


def load_curated_outputs(outputs: dict[str, str], stage_prefix: str, settings: Settings | None = None) -> None:
    put_parquet_to_stage(outputs["telemetry_enriched"], "TELEMETRY_INTERNAL_STAGE", settings, stage_prefix)
    put_parquet_to_stage(outputs["vehicle_hourly_metrics"], "TELEMETRY_INTERNAL_STAGE", settings, stage_prefix)
    truncate_table("TELEMETRY_ENRICHED_STAGE", settings)
    truncate_table("VEHICLE_HOURLY_METRICS_STAGE", settings)
    copy_parquet_from_stage(
        "TELEMETRY_ENRICHED_STAGE",
        "TELEMETRY_INTERNAL_STAGE",
        stage_prefix,
        ".*telemetry_enriched[.]parquet",
        settings,
    )
    copy_parquet_from_stage(
        "VEHICLE_HOURLY_METRICS_STAGE",
        "TELEMETRY_INTERNAL_STAGE",
        stage_prefix,
        ".*vehicle_hourly_metrics[.]parquet",
        settings,
    )
    merge_stage_table("TELEMETRY_ENRICHED", "TELEMETRY_ENRICHED_STAGE", ["EVENT_ID"], settings)
    merge_stage_table(
        "VEHICLE_HOURLY_METRICS",
        "VEHICLE_HOURLY_METRICS_STAGE",
        ["VIN", "EVENT_DATE", "EVENT_HOUR"],
        settings,
    )


def truncate_table(table_name: str, settings: Settings | None = None) -> None:
    table = _identifier(table_name)
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table}")


def fetch_processed_s3_keys(settings: Settings | None = None) -> set[str]:
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT S3_KEY FROM PROCESSED_S3_OBJECTS")
            return {row[0] for row in cur.fetchall()}


def mark_s3_objects_processed(keys: list[str], dag_run_id: str, settings: Settings | None = None) -> None:
    if not keys:
        return
    with snowflake_connection(settings) as conn:
        with conn.cursor() as cur:
            for key in keys:
                cur.execute(
                    """
                    MERGE INTO PROCESSED_S3_OBJECTS AS target
                    USING (SELECT %s AS S3_KEY, %s AS DAG_RUN_ID) AS source
                    ON target.S3_KEY = source.S3_KEY
                    WHEN MATCHED THEN UPDATE SET
                        DAG_RUN_ID = source.DAG_RUN_ID,
                        PROCESSED_AT = CURRENT_TIMESTAMP()
                    WHEN NOT MATCHED THEN INSERT (S3_KEY, DAG_RUN_ID)
                    VALUES (source.S3_KEY, source.DAG_RUN_ID)
                    """,
                    (key, dag_run_id),
                )


def _table_columns(cur, table_name: str) -> list[str]:
    cur.execute(f"DESCRIBE TABLE {table_name}")
    return [
        row[0]
        for row in cur.fetchall()
        if row[0].upper() not in {"LOADED_AT", "INGESTED_AT"}
    ]


def _identifier(value: str) -> str:
    if not SNOWFLAKE_IDENTIFIER.match(value):
        raise ValueError(f"Invalid Snowflake identifier: {value}")
    return value.upper()


def _stage_reference(stage_name: str, stage_prefix: str | None = None) -> str:
    stage = f"@{_identifier(stage_name)}"
    if stage_prefix:
        cleaned_prefix = stage_prefix.strip("/").replace("'", "")
        return f"{stage}/{cleaned_prefix}"
    return stage
