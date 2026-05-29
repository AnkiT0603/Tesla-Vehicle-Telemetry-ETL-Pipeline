from pathlib import Path

import boto3

from telemetry_etl.config import Settings, get_settings


def list_s3_objects(settings: Settings | None = None, prefix: str | None = None) -> list[str]:
    cfg = settings or get_settings()
    s3 = boto3.client("s3", region_name=cfg.aws_region)
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=cfg.s3_bucket, Prefix=prefix or cfg.s3_raw_prefix):
        for item in page.get("Contents", []):
            keys.append(item["Key"])
    return keys


def download_s3_object(key: str, destination_dir: str | Path, settings: Settings | None = None) -> str:
    cfg = settings or get_settings()
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    local_path = destination / Path(key).name
    s3 = boto3.client("s3", region_name=cfg.aws_region)
    s3.download_file(cfg.s3_bucket, key, str(local_path))
    return str(local_path)

