from __future__ import annotations

from collections import defaultdict

from rbccps_measurement.contracts.output_schema import MeasurementReport


def aggregate_by_lamp_track(reports: list[MeasurementReport]) -> dict[str, list[MeasurementReport]]:
    grouped: dict[str, list[MeasurementReport]] = defaultdict(list)
    for report in reports:
        grouped[report.lamp_track_id].append(report)
    return dict(grouped)
