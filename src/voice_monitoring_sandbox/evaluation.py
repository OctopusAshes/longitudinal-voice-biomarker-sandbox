"""Repeated simulation and monitoring-performance summaries."""

from dataclasses import dataclass

import numpy as np

from .config import SimulationConfig
from .detection import detect_change
from .simulation import simulate_trajectory


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Aggregate results across evaluable Monte Carlo runs."""

    requested_runs: int
    evaluable_runs: int
    detection_probability: float | None
    missed_change_rate: float | None
    false_alert_probability: float | None
    median_detection_delay: float | None
    detection_delay_q1: float | None
    detection_delay_q3: float | None

    def to_dict(self) -> dict[str, int | float | None]:
        return {
            "requested_runs": self.requested_runs,
            "evaluable_runs": self.evaluable_runs,
            "detection_probability": self.detection_probability,
            "missed_change_rate": self.missed_change_rate,
            "false_alert_probability": self.false_alert_probability,
            "median_detection_delay": self.median_detection_delay,
            "detection_delay_q1": self.detection_delay_q1,
            "detection_delay_q3": self.detection_delay_q3,
        }


def evaluate_simulations(
    config: SimulationConfig,
    rng: np.random.Generator,
) -> EvaluationSummary:
    """Estimate detection behavior by repeatedly sampling the same scenario."""
    detected = 0
    missed = 0
    false_alerts = 0
    delays: list[int] = []
    evaluable = 0

    for _ in range(config.simulations):
        result = detect_change(simulate_trajectory(config, rng), config)
        if not result.evaluable:
            continue
        evaluable += 1
        false_alerts += int(result.false_alert_before_change)
        if result.change_detected:
            detected += 1
            delays.append(result.detection_delay or 0)
        else:
            missed += 1

    if evaluable == 0:
        return EvaluationSummary(
            config.simulations, 0, None, None, None, None, None, None
        )

    median = q1 = q3 = None
    if delays:
        quantiles = np.quantile(delays, [0.25, 0.5, 0.75])
        q1, median, q3 = (float(value) for value in quantiles)

    return EvaluationSummary(
        requested_runs=config.simulations,
        evaluable_runs=evaluable,
        detection_probability=detected / evaluable,
        missed_change_rate=missed / evaluable,
        false_alert_probability=false_alerts / evaluable,
        median_detection_delay=median,
        detection_delay_q1=q1,
        detection_delay_q3=q3,
    )
