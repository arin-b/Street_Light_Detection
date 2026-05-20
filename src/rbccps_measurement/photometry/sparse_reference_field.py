from __future__ import annotations

from rbccps_measurement.contracts.calibration_policy import CalibrationDecision


def physical_estimates_allowed(decision: CalibrationDecision) -> bool:
    return decision.physical_allowed
