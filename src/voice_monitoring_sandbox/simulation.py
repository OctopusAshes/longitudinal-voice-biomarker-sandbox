"""Synthetic longitudinal trajectory generation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import GRADUAL_CHANGE_DAYS, ChangeType, SimulationConfig


@dataclass(frozen=True, slots=True)
class Trajectory:
    """One simulated daily measurement trajectory."""

    days: np.ndarray
    underlying_change: np.ndarray
    within_person_variation: np.ndarray
    measurement_noise: np.ndarray
    observed: np.ndarray
    missing: np.ndarray

    def to_frame(self) -> pd.DataFrame:
        """Return trajectory components as a table."""
        return pd.DataFrame(
            {
                "day": self.days,
                "underlying_change": self.underlying_change,
                "within_person_variation": self.within_person_variation,
                "measurement_noise": self.measurement_noise,
                "observed_value": self.observed,
                "missing": self.missing,
            }
        )


def _underlying_change(config: SimulationConfig, days: np.ndarray) -> np.ndarray:
    signed_magnitude = config.change_direction.sign * config.change_magnitude
    if config.change_type is ChangeType.ABRUPT:
        return np.where(days >= config.change_day, signed_magnitude, 0.0)

    progress = np.clip(
        (days - config.change_day + 1) / GRADUAL_CHANGE_DAYS,
        0.0,
        1.0,
    )
    return signed_magnitude * progress


def simulate_trajectory(
    config: SimulationConfig,
    rng: np.random.Generator,
) -> Trajectory:
    """Generate one trajectory from a validated configuration."""
    days = np.arange(1, config.monitoring_days + 1)
    change = _underlying_change(config, days)
    within = rng.normal(0.0, config.within_person_sd, config.monitoring_days)
    measurement = rng.normal(0.0, config.measurement_sd, config.monitoring_days)
    missing = rng.random(config.monitoring_days) < config.missing_probability
    observed = np.where(missing, np.nan, change + within + measurement)
    return Trajectory(days, change, within, measurement, observed, missing)
