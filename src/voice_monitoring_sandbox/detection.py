"""Personal baseline estimation and transparent threshold detection."""

from dataclasses import dataclass

import numpy as np

from .config import MIN_BASELINE_OBSERVATIONS, ChangeDirection, SimulationConfig
from .simulation import Trajectory


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Detector outputs for one trajectory."""

    evaluable: bool
    baseline_observations: int
    baseline_mean: float | None
    baseline_sd: float | None
    threshold_value: float | None
    z_scores: np.ndarray
    exceedances: np.ndarray
    alerts: np.ndarray
    first_post_change_alert: int | None
    detection_delay: int | None
    false_alert_before_change: bool

    @property
    def change_detected(self) -> bool:
        return self.first_post_change_alert is not None

    @property
    def missed_change(self) -> bool:
        return self.evaluable and not self.change_detected


def _not_evaluable(length: int, baseline_observations: int) -> DetectionResult:
    return DetectionResult(
        evaluable=False,
        baseline_observations=baseline_observations,
        baseline_mean=None,
        baseline_sd=None,
        threshold_value=None,
        z_scores=np.full(length, np.nan),
        exceedances=np.zeros(length, dtype=bool),
        alerts=np.zeros(length, dtype=bool),
        first_post_change_alert=None,
        detection_delay=None,
        false_alert_before_change=False,
    )


def detect_change(
    trajectory: Trajectory,
    config: SimulationConfig,
) -> DetectionResult:
    """Apply the specified personal-baseline alert rule to one trajectory."""
    baseline_mask = (trajectory.days <= config.baseline_days) & ~trajectory.missing
    baseline_values = trajectory.observed[baseline_mask]
    baseline_count = int(baseline_values.size)
    if baseline_count < MIN_BASELINE_OBSERVATIONS:
        return _not_evaluable(len(trajectory.days), baseline_count)

    baseline_mean = float(np.mean(baseline_values))
    baseline_sd = float(np.std(baseline_values, ddof=1))
    if not np.isfinite(baseline_sd) or baseline_sd <= np.finfo(float).eps:
        return _not_evaluable(len(trajectory.days), baseline_count)

    z_scores = (trajectory.observed - baseline_mean) / baseline_sd
    if config.change_direction is ChangeDirection.INCREASE:
        exceedances = z_scores > config.alert_threshold
        threshold_value = baseline_mean + config.alert_threshold * baseline_sd
    else:
        exceedances = z_scores < -config.alert_threshold
        threshold_value = baseline_mean - config.alert_threshold * baseline_sd

    exceedances = np.where(trajectory.days > config.baseline_days, exceedances, False)
    exceedances = np.where(trajectory.missing, False, exceedances)
    alerts = np.zeros(len(trajectory.days), dtype=bool)
    consecutive = 0
    for index, exceeded in enumerate(exceedances):
        if trajectory.missing[index] or not exceeded:
            consecutive = 0
            continue
        consecutive += 1
        if consecutive == config.confirmations_required:
            alerts[index] = True

    alert_days = trajectory.days[alerts]
    false_alert = bool(np.any(alert_days < config.change_day))
    post_change = alert_days[alert_days >= config.change_day]
    first_alert = int(post_change[0]) if post_change.size else None
    delay = first_alert - config.change_day if first_alert is not None else None

    return DetectionResult(
        evaluable=True,
        baseline_observations=baseline_count,
        baseline_mean=baseline_mean,
        baseline_sd=baseline_sd,
        threshold_value=float(threshold_value),
        z_scores=z_scores,
        exceedances=exceedances,
        alerts=alerts,
        first_post_change_alert=first_alert,
        detection_delay=delay,
        false_alert_before_change=false_alert,
    )
