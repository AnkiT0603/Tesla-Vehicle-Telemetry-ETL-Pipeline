from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class QualityResult:
    passed: bool
    total_records: int
    failed_records: int
    checks: dict[str, int]


def run_quality_checks(df: pd.DataFrame) -> QualityResult:
    invalid_masks = {
        "missing_event_id": df["event_id"].isna(),
        "missing_vin": df["vin"].isna(),
        "invalid_battery_pct": ~df["battery_pct"].between(0, 100),
        "invalid_speed_mph": ~df["speed_mph"].between(0, 180),
        "invalid_latitude": ~df["latitude"].between(-90, 90),
        "invalid_longitude": ~df["longitude"].between(-180, 180),
        "negative_odometer": df["odometer_miles"] < 0,
        "duplicate_event_id": df["event_id"].duplicated(),
    }
    checks = {
        name: int(mask.sum()) for name, mask in invalid_masks.items()
    }
    failed_records = int(pd.concat(invalid_masks.values(), axis=1).any(axis=1).sum())
    return QualityResult(
        passed=all(value == 0 for value in checks.values()),
        total_records=len(df),
        failed_records=failed_records,
        checks=checks,
    )


def assert_quality(result: QualityResult) -> None:
    if not result.passed:
        raise ValueError(f"Telemetry quality checks failed: {result.checks}")
