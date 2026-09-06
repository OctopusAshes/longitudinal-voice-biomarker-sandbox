"""End-to-end orchestration and export helpers."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .config import SimulationConfig
from .detection import DetectionResult, detect_change
from .evaluation import EvaluationSummary, evaluate_simulations
from .simulation import Trajectory, simulate_trajectory


@dataclass(frozen=True, slots=True)
class SandboxResult:
    """Example trajectory and repeated-simulation results for one configuration."""

    config: SimulationConfig
    trajectory: Trajectory
    detection: DetectionResult
    evaluation: EvaluationSummary


def run_sandbox(config: SimulationConfig) -> SandboxResult:
    """Run one display trajectory and an independent Monte Carlo evaluation."""
    example_seed, evaluation_seed = np.random.SeedSequence(config.random_seed).spawn(2)
    trajectory = simulate_trajectory(config, np.random.default_rng(example_seed))
    detection = detect_change(trajectory, config)
    evaluation = evaluate_simulations(config, np.random.default_rng(evaluation_seed))
    return SandboxResult(config, trajectory, detection, evaluation)


def summary_payload(result: SandboxResult) -> dict[str, object]:
    """Build the JSON-serializable summary described in the project plan."""
    detection = result.detection
    return {
        "configuration": asdict(result.config),
        "example_trajectory": {
            "true_change_day": result.config.change_day,
            "first_post_change_alert": detection.first_post_change_alert,
            "detection_delay": detection.detection_delay,
            "false_alert_before_change": detection.false_alert_before_change,
            "evaluable": detection.evaluable,
        },
        "repeated_simulation": result.evaluation.to_dict(),
    }


def write_exports(
    result: SandboxResult,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Write the example CSV and simulation-summary JSON files."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    frame = result.trajectory.to_frame()
    frame["z_score"] = result.detection.z_scores
    frame["threshold_exceeded"] = result.detection.exceedances
    frame["alert"] = result.detection.alerts

    csv_path = destination / "example_trajectory.csv"
    json_path = destination / "simulation_summary.json"
    frame.to_csv(csv_path, index=False)
    json_path.write_text(
        json.dumps(summary_payload(result), indent=2),
        encoding="utf-8",
    )
    return csv_path, json_path
