import unittest

import numpy as np

from voice_monitoring_sandbox.config import (
    ChangeDirection,
    ChangeType,
    SimulationConfig,
)
from voice_monitoring_sandbox.simulation import simulate_trajectory


class SimulationTests(unittest.TestCase):
    def test_fixed_seed_is_reproducible(self) -> None:
        config = SimulationConfig()
        first = simulate_trajectory(config, np.random.default_rng(12))
        second = simulate_trajectory(config, np.random.default_rng(12))
        np.testing.assert_allclose(first.observed, second.observed, equal_nan=True)
        np.testing.assert_array_equal(first.missing, second.missing)

    def test_abrupt_change_starts_on_selected_day(self) -> None:
        config = SimulationConfig(
            change_day=20,
            change_magnitude=2.0,
            change_direction=ChangeDirection.DECREASE,
            change_type=ChangeType.ABRUPT,
            missing_probability=0,
        )
        trajectory = simulate_trajectory(config, np.random.default_rng(0))
        self.assertTrue(np.all(trajectory.underlying_change[:19] == 0))
        self.assertTrue(np.all(trajectory.underlying_change[19:] == -2.0))

    def test_gradual_change_reaches_magnitude_in_seven_days(self) -> None:
        config = SimulationConfig(
            change_day=20,
            change_magnitude=1.4,
            change_type=ChangeType.GRADUAL,
            missing_probability=0,
        )
        trajectory = simulate_trajectory(config, np.random.default_rng(0))
        self.assertAlmostEqual(trajectory.underlying_change[19], 0.2)
        self.assertAlmostEqual(trajectory.underlying_change[25], 1.4)
        self.assertAlmostEqual(trajectory.underlying_change[-1], 1.4)

    def test_change_must_follow_baseline(self) -> None:
        with self.assertRaises(ValueError):
            SimulationConfig(baseline_days=14, change_day=14)

    def test_combined_variability_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            SimulationConfig(within_person_sd=0, measurement_sd=0)


if __name__ == "__main__":
    unittest.main()
