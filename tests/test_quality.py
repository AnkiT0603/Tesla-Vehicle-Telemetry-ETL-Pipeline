import pandas as pd

from telemetry_etl.quality import run_quality_checks


def test_quality_checks_pass_for_valid_records():
    df = pd.DataFrame(
        [
            {
                "event_id": "evt-1",
                "vin": "5YJ3E1EA7KF317001",
                "battery_pct": 50,
                "speed_mph": 35,
                "latitude": 10,
                "longitude": 20,
                "odometer_miles": 100,
            }
        ]
    )

    result = run_quality_checks(df)

    assert result.passed is True
    assert result.failed_records == 0


def test_quality_checks_fail_for_invalid_battery():
    df = pd.DataFrame(
        [
            {
                "event_id": "evt-1",
                "vin": "5YJ3E1EA7KF317001",
                "battery_pct": 120,
                "speed_mph": 35,
                "latitude": 10,
                "longitude": 20,
                "odometer_miles": 100,
            }
        ]
    )

    result = run_quality_checks(df)

    assert result.passed is False
    assert result.checks["invalid_battery_pct"] == 1
    assert result.failed_records == 1


def test_failed_records_counts_rows_not_check_totals():
    df = pd.DataFrame(
        [
            {
                "event_id": "evt-1",
                "vin": "5YJ3E1EA7KF317001",
                "battery_pct": 120,
                "speed_mph": 200,
                "latitude": 10,
                "longitude": 20,
                "odometer_miles": 100,
            },
            {
                "event_id": "evt-2",
                "vin": "5YJ3E1EA7KF317002",
                "battery_pct": 40,
                "speed_mph": 35,
                "latitude": 95,
                "longitude": 20,
                "odometer_miles": 100,
            },
        ]
    )

    result = run_quality_checks(df)

    assert result.passed is False
    assert result.failed_records == 2
