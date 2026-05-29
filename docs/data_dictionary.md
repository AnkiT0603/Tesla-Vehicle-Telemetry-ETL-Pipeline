# Data Dictionary

## Telemetry Event

| Column | Type | Description |
| --- | --- | --- |
| event_id | string | Unique telemetry event identifier. |
| vin | string | Vehicle identification number. |
| vehicle_model | string | Tesla model name. |
| event_ts | timestamp | UTC event timestamp. |
| latitude | float | Vehicle latitude. |
| longitude | float | Vehicle longitude. |
| speed_mph | float | Vehicle speed in miles per hour. |
| battery_pct | float | Battery state of charge percentage. |
| odometer_miles | float | Vehicle odometer reading. |
| power_kw | float | Positive when charging, negative when consuming. |
| charging_state | string | Current state: charging, driving, parked, or idle. |
| tire_pressure_fl | float | Front-left tire pressure in PSI. |
| tire_pressure_fr | float | Front-right tire pressure in PSI. |
| tire_pressure_rl | float | Rear-left tire pressure in PSI. |
| tire_pressure_rr | float | Rear-right tire pressure in PSI. |
| outside_temp_f | float | Outside temperature in Fahrenheit. |

## Derived Fields

| Column | Description |
| --- | --- |
| event_date | Date extracted from event timestamp. |
| event_hour | Hour extracted from event timestamp. |
| is_moving | True when speed is greater than 1 mph. |
| is_low_battery | True when battery is below 20 percent. |
| avg_tire_pressure | Average of four tire pressure readings. |
| has_tire_pressure_alert | True when average tire pressure is below 32 PSI. |
| energy_mode | charging, consuming, or neutral based on power draw. |

