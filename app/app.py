"""Single-page Gradio interface for the synthetic monitoring sandbox."""

import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from voice_monitoring_sandbox import (
    ChangeDirection,
    ChangeType,
    SimulationConfig,
    run_sandbox,
    write_exports,
)
from voice_monitoring_sandbox.plotting import plot_trajectory


def _display_value(value: float | None, *, percent: bool = False) -> str:
    if value is None:
        return "Not available"
    if percent:
        return f"{value:.1%}"
    return f"{value:.1f} days"


def _run(
    monitoring_days: float,
    baseline_days: float,
    change_day: float,
    change_magnitude: float,
    change_direction: str,
    change_type: str,
    within_person_sd: float,
    measurement_sd: float,
    missing_probability: float,
    alert_threshold: float,
    confirmations_required: float,
    simulations: float,
    random_seed: float,
):
    try:
        config = SimulationConfig(
            monitoring_days=int(monitoring_days),
            baseline_days=int(baseline_days),
            change_day=int(change_day),
            change_magnitude=float(change_magnitude),
            change_direction=ChangeDirection(change_direction.lower()),
            change_type=ChangeType(change_type.lower()),
            within_person_sd=float(within_person_sd),
            measurement_sd=float(measurement_sd),
            missing_probability=float(missing_probability),
            alert_threshold=float(alert_threshold),
            confirmations_required=int(confirmations_required),
            simulations=int(simulations),
            random_seed=int(random_seed),
        )
    except (TypeError, ValueError) as error:
        raise gr.Error(str(error)) from error

    result = run_sandbox(config)
    detection = result.detection
    evaluation = result.evaluation
    example_summary = (
        f"**True change day:** {config.change_day}  \n"
        f"**First post-change alert:** "
        f"{detection.first_post_change_alert or 'None'}  \n"
        f"**Detection delay:** "
        f"{_display_value(detection.detection_delay)}  \n"
        f"**False alert before change:** "
        f"{'Yes' if detection.false_alert_before_change else 'No'}"
    )

    delay_iqr = "Not available"
    if evaluation.detection_delay_q1 is not None:
        delay_iqr = (
            f"{evaluation.detection_delay_q1:.1f}–"
            f"{evaluation.detection_delay_q3:.1f} days"
        )
    repeated_summary = pd.DataFrame(
        {
            "Output": [
                "Evaluable runs",
                "Detection probability",
                "Missed-change rate",
                "False-alert probability",
                "Median detection delay",
                "Detection-delay IQR",
            ],
            "Result": [
                f"{evaluation.evaluable_runs} / {evaluation.requested_runs}",
                _display_value(evaluation.detection_probability, percent=True),
                _display_value(evaluation.missed_change_rate, percent=True),
                _display_value(evaluation.false_alert_probability, percent=True),
                _display_value(evaluation.median_detection_delay),
                delay_iqr,
            ],
        }
    )

    output_dir = Path(tempfile.mkdtemp(prefix="voice-sandbox-"))
    csv_path, json_path = write_exports(result, output_dir)
    return (
        plot_trajectory(result),
        example_summary,
        repeated_summary,
        str(csv_path),
        str(json_path),
    )


def build_demo() -> gr.Blocks:
    """Build the planned single-page interface."""
    with gr.Blocks(title="Longitudinal Voice Biomarker Sandbox") as demo:
        gr.Markdown(
            "# Longitudinal Voice Biomarker Sandbox\n"
            "A synthetic sandbox for exploring longitudinal monitoring assumptions."
        )
        with gr.Row():
            with gr.Column(scale=1):
                monitoring_days = gr.Number(60, precision=0, label="Monitoring days")
                baseline_days = gr.Number(14, precision=0, label="Baseline days")
                change_day = gr.Number(30, precision=0, label="Change day")
                change_magnitude = gr.Number(1.5, label="Change magnitude")
                change_direction = gr.Dropdown(
                    ["Increase", "Decrease"], value="Increase", label="Change direction"
                )
                change_type = gr.Dropdown(
                    ["Abrupt", "Gradual"], value="Gradual", label="Change type"
                )
                within_person_sd = gr.Number(
                    0.5, label="Within-person variability (SD)"
                )
                measurement_sd = gr.Number(0.3, label="Measurement noise (SD)")
                missing_probability = gr.Number(0.10, label="Missing probability")
                alert_threshold = gr.Number(2.0, label="Alert threshold (baseline SDs)")
                confirmations_required = gr.Number(
                    2, precision=0, label="Confirmations required"
                )
                simulations = gr.Number(500, precision=0, label="Simulations")
                random_seed = gr.Number(0, precision=0, label="Random seed")
                run_button = gr.Button("Run simulation", variant="primary")

            with gr.Column(scale=2):
                plot = gr.Plot(label="Example trajectory")
                example_summary = gr.Markdown()
                repeated_summary = gr.Dataframe(
                    headers=["Output", "Result"],
                    datatype=["str", "str"],
                    interactive=False,
                    label="Repeated simulation summary",
                )
                with gr.Row():
                    csv_download = gr.File(label="Example trajectory CSV")
                    json_download = gr.File(label="Simulation summary JSON")

        run_button.click(
            fn=_run,
            inputs=[
                monitoring_days,
                baseline_days,
                change_day,
                change_magnitude,
                change_direction,
                change_type,
                within_person_sd,
                measurement_sd,
                missing_probability,
                alert_threshold,
                confirmations_required,
                simulations,
                random_seed,
            ],
            outputs=[
                plot,
                example_summary,
                repeated_summary,
                csv_download,
                json_download,
            ],
        )
    return demo


if __name__ == "__main__":
    build_demo().launch()
