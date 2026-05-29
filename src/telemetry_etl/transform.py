from pathlib import Path
import sys

import pandas as pd

from telemetry_etl.quality import assert_quality, run_quality_checks
from telemetry_etl.schemas import TelemetryEvent


def read_jsonl(path: str | Path) -> pd.DataFrame:
    rows = []
    for record in pd.read_json(path, lines=True).to_dict(orient="records"):
        rows.append(TelemetryEvent(**record).model_dump())
    return pd.DataFrame(rows)


def enrich_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["event_ts"] = pd.to_datetime(enriched["event_ts"], utc=True)
    enriched["event_date"] = enriched["event_ts"].dt.date.astype(str)
    enriched["event_hour"] = enriched["event_ts"].dt.hour
    enriched["is_moving"] = enriched["speed_mph"] > 1
    enriched["is_low_battery"] = enriched["battery_pct"] < 20
    enriched["avg_tire_pressure"] = enriched[
        ["tire_pressure_fl", "tire_pressure_fr", "tire_pressure_rl", "tire_pressure_rr"]
    ].mean(axis=1)
    enriched["has_tire_pressure_alert"] = enriched["avg_tire_pressure"] < 32
    enriched["energy_mode"] = enriched["power_kw"].apply(_energy_mode)
    return enriched


def build_vehicle_hourly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        df.groupby(["vin", "vehicle_model", "event_date", "event_hour"], as_index=False)
        .agg(
            events=("event_id", "count"),
            avg_speed_mph=("speed_mph", "mean"),
            max_speed_mph=("speed_mph", "max"),
            avg_battery_pct=("battery_pct", "mean"),
            min_battery_pct=("battery_pct", "min"),
            max_odometer_miles=("odometer_miles", "max"),
            low_battery_events=("is_low_battery", "sum"),
            tire_pressure_alerts=("has_tire_pressure_alert", "sum"),
        )
        .round(2)
    )
    return metrics


def _energy_mode(power_kw: float) -> str:
    if power_kw > 5:
        return "charging"
    if power_kw < -5:
        return "consuming"
    return "neutral"


def transform_file(input_path: str | Path, output_dir: str | Path) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    raw = read_jsonl(input_path)
    quality = run_quality_checks(raw)
    assert_quality(quality)

    enriched = enrich_telemetry(raw)
    metrics = build_vehicle_hourly_metrics(enriched)

    enriched_path = output / "telemetry_enriched.parquet"
    metrics_path = output / "vehicle_hourly_metrics.parquet"
    enriched.to_parquet(enriched_path, index=False)
    metrics.to_parquet(metrics_path, index=False)

    return {
        "enriched": str(enriched_path),
        "vehicle_hourly_metrics": str(metrics_path),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m telemetry_etl.transform <input_jsonl> <output_dir>")
    outputs = transform_file(sys.argv[1], sys.argv[2])
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()

