"""Configuration and validation for the synthetic monitoring sandbox."""

from dataclasses import dataclass
from enum import StrEnum

MIN_BASELINE_OBSERVATIONS = 5
GRADUAL_CHANGE_DAYS = 7


class ChangeDirection(StrEnum):
    """Direction of the simulated underlying change."""

    INCREASE = "increase"
    DECREASE = "decrease"

    @property
    def sign(self) -> int:
        return 1 if self is ChangeDirection.INCREASE else -1


class ChangeType(StrEnum):
    """Shape of the simulated underlying change."""

    ABRUPT = "abrupt"
    GRADUAL = "gradual"


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Validated settings shared by simulation, detection, and evaluation."""

    monitoring_days: int = 60
    baseline_days: int = 14
    change_day: int = 30
    change_magnitude: float = 1.5
    change_direction: ChangeDirection = ChangeDirection.INCREASE
    change_type: ChangeType = ChangeType.GRADUAL
    within_person_sd: float = 0.5
    measurement_sd: float = 0.3
    missing_probability: float = 0.10
    alert_threshold: float = 2.0
    confirmations_required: int = 2
    simulations: int = 500
    random_seed: int = 0

    def __post_init__(self) -> None:
        if self.monitoring_days < 6:
            raise ValueError("Monitoring days must be at least 6.")
        if self.baseline_days < MIN_BASELINE_OBSERVATIONS:
            raise ValueError(
                f"Baseline days must be at least {MIN_BASELINE_OBSERVATIONS}."
            )
        if not self.baseline_days < self.change_day <= self.monitoring_days:
            raise ValueError(
                "Change day must be after the baseline period and within monitoring."
            )
        if self.change_magnitude <= 0:
            raise ValueError("Change magnitude must be greater than zero.")
        if self.within_person_sd < 0 or self.measurement_sd < 0:
            raise ValueError("Variability settings cannot be negative.")
        if self.within_person_sd == 0 and self.measurement_sd == 0:
            raise ValueError(
                "Combined simulated variability must be greater than zero."
            )
        if not 0 <= self.missing_probability <= 1:
            raise ValueError("Missing probability must be between 0 and 1.")
        if self.alert_threshold <= 0:
            raise ValueError("Alert threshold must be greater than zero.")
        if self.confirmations_required < 1:
            raise ValueError("Confirmations required must be at least 1.")
        if self.simulations < 1:
            raise ValueError("Simulations must be at least 1.")
        if self.random_seed < 0:
            raise ValueError("Random seed cannot be negative.")
