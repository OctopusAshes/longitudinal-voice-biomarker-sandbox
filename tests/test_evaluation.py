import unittest

import numpy as np

from voice_monitoring_sandbox.config import SimulationConfig
from voice_monitoring_sandbox.evaluation import evaluate_simulations


class EvaluationTests(unittest.TestCase):
    def test_probabilities_are_between_zero_and_one(self) -> None:
        config = SimulationConfig(simulations=100, missing_probability=0.2)
        summary = evaluate_simulations(config, np.random.default_rng(5))
        self.assertGreater(summary.evaluable_runs, 0)
        for probability in (
            summary.detection_probability,
            summary.missed_change_rate,
            summary.false_alert_probability,
        ):
            self.assertIsNotNone(probability)
            self.assertGreaterEqual(probability, 0)
            self.assertLessEqual(probability, 1)

    def test_repeated_evaluation_is_reproducible(self) -> None:
        config = SimulationConfig(simulations=50)
        first = evaluate_simulations(config, np.random.default_rng(18))
        second = evaluate_simulations(config, np.random.default_rng(18))
        self.assertEqual(first, second)

    def test_detection_and_missed_rates_sum_to_one(self) -> None:
        config = SimulationConfig(simulations=50)
        summary = evaluate_simulations(config, np.random.default_rng(22))
        self.assertAlmostEqual(
            summary.detection_probability + summary.missed_change_rate,
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
