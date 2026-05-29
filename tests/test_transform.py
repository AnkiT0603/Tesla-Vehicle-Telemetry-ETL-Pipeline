from pathlib import Path

from telemetry_etl.transform import build_vehicle_hourly_metrics, enrich_telemetry, read_jsonl


SAMPLE_PATH = Path("data/sample/tesla_telemetry_sample.jsonl")


def test_read_jsonl_validates_sample_data():
    df = read_jsonl(SAMPLE_PATH)

    assert len(df) == 5
    assert set(df["vehicle_model"]) == {"Model 3", "Model Y", "Model X"}


def test_enrich_telemetry_adds_monitoring_flags():
    df = enrich_telemetry(read_jsonl(SAMPLE_PATH))

    assert "is_low_battery" in df.columns
    assert "has_tire_pressure_alert" in df.columns
    assert df["is_low_battery"].sum() == 1
    assert df["has_tire_pressure_alert"].sum() == 2


def test_build_vehicle_hourly_metrics_groups_by_vehicle_hour():
    df = enrich_telemetry(read_jsonl(SAMPLE_PATH))
    metrics = build_vehicle_hourly_metrics(df)

    assert len(metrics) == 3
    assert "avg_speed_mph" in metrics.columns

