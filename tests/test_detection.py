import unittest

import numpy as np

from voice_monitoring_sandbox.config import ChangeDirection, SimulationConfig
from voice_monitoring_sandbox.detection import detect_change
from voice_monitoring_sandbox.simulation import Trajectory, simulate_trajectory


def make_trajectory(
    values: list[float],
    missing: list[bool] | None = None,
) -> Trajectory:
    observed = np.asarray(values, dtype=float)
    missing_array = np.zeros(len(values), dtype=bool)
    if missing is not None:
        missing_array = np.asarray(missing, dtype=bool)
        observed = np.where(missing_array, np.nan, observed)
    zeros = np.zeros(len(values), dtype=float)
    return Trajectory(
        days=np.arange(1, len(values) + 1),
        underlying_change=zeros,
        within_person_variation=zeros,
        measurement_noise=zeros,
        observed=observed,
        missing=missing_array,
    )


class DetectionTests(unittest.TestCase):
    def test_large_change_is_detected_under_low_noise(self) -> None:
        config = SimulationConfig(
            baseline_days=14,
            change_day=20,
            change_magnitude=10,
            within_person_sd=0.05,
            measurement_sd=0.05,
            missing_probability=0,
            confirmations_required=2,
        )
        trajectory = simulate_trajectory(config, np.random.default_rng(7))
        result = detect_change(trajectory, config)
        self.assertEqual(result.first_post_change_alert, 21)
        self.assertGreaterEqual(result.detection_delay, 0)

    def test_confirmation_requires_consecutive_exceedances(self) -> None:
        config = SimulationConfig(
            monitoring_days=10,
            baseline_days=5,
            change_day=8,
            alert_threshold=2,
            confirmations_required=2,
            within_person_sd=1,
            measurement_sd=0,
        )
        result = detect_change(
            make_trajectory([-1, -0.5, 0, 0.5, 1, 3, 0, 3, 3, 0]),
            config,
        )
        self.assertEqual(result.first_post_change_alert, 9)
        self.assertEqual(int(np.sum(result.alerts)), 1)

    def test_missing_observation_breaks_confirmation(self) -> None:
        config = SimulationConfig(
            monitoring_days=10,
            baseline_days=5,
            change_day=8,
            alert_threshold=2,
            confirmations_required=2,
            within_person_sd=1,
            measurement_sd=0,
        )
        trajectory = make_trajectory(
            [-1, -0.5, 0, 0.5, 1, 3, 3, 3, 3, 0],
            [False, False, False, False, False, False, True, False, False, False],
        )
        result = detect_change(trajectory, config)
        self.assertFalse(result.alerts[5])
        self.assertFalse(result.alerts[7])
        self.assertTrue(result.alerts[8])

    def test_decrease_uses_negative_threshold(self) -> None:
        config = SimulationConfig(
            monitoring_days=8,
            baseline_days=5,
            change_day=7,
            change_direction=ChangeDirection.DECREASE,
            alert_threshold=2,
            confirmations_required=1,
            within_person_sd=1,
            measurement_sd=0,
        )
        result = detect_change(
            make_trajectory([-1, -0.5, 0, 0.5, 1, 0, -3, -3]),
            config,
        )
        self.assertEqual(result.first_post_change_alert, 7)
        self.assertEqual(result.detection_delay, 0)

    def test_fewer_than_five_baseline_values_is_not_evaluable(self) -> None:
        config = SimulationConfig(
            monitoring_days=8,
            baseline_days=5,
            change_day=7,
            within_person_sd=1,
            measurement_sd=0,
        )
        trajectory = make_trajectory(
            [-1, -0.5, 0, 0.5, 1, 0, 3, 3],
            [True, False, False, False, False, False, False, False],
        )
        result = detect_change(trajectory, config)
        self.assertFalse(result.evaluable)
        self.assertEqual(result.baseline_observations, 4)


if __name__ == "__main__":
    unittest.main()
