"""Plotting for an example synthetic trajectory."""

import numpy as np
import plotly.graph_objects as go

from .pipeline import SandboxResult


def plot_trajectory(result: SandboxResult) -> go.Figure:
    """Plot observations, missing days, baseline, threshold, and change timing."""
    trajectory = result.trajectory
    detection = result.detection
    config = result.config

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=trajectory.days,
            y=trajectory.observed,
            mode="lines+markers",
            name="Observed measurement",
            connectgaps=False,
        )
    )
    figure.add_trace(
        go.Scatter(
            x=trajectory.days,
            y=trajectory.underlying_change,
            mode="lines",
            line={"dash": "dash"},
            name="Underlying change",
        )
    )

    finite = trajectory.observed[np.isfinite(trajectory.observed)]
    anchor = float(np.min(finite)) if finite.size else 0.0
    missing_y = anchor - max(float(np.ptp(finite)) * 0.08 if finite.size else 0.0, 0.15)
    if np.any(trajectory.missing):
        figure.add_trace(
            go.Scatter(
                x=trajectory.days[trajectory.missing],
                y=np.full(np.sum(trajectory.missing), missing_y),
                mode="markers",
                marker={"symbol": "x", "size": 9},
                name="Missing recording",
                hovertemplate="Day %{x}: missing<extra></extra>",
            )
        )

    if detection.evaluable:
        figure.add_hline(
            y=detection.baseline_mean,
            line_dash="dot",
            annotation_text="Estimated baseline",
        )
        figure.add_hline(
            y=detection.threshold_value,
            line_dash="dot",
            line_color="#d62728",
            annotation_text="Alert threshold",
        )

    if np.any(detection.alerts):
        indices = np.flatnonzero(detection.alerts)
        figure.add_trace(
            go.Scatter(
                x=trajectory.days[indices],
                y=trajectory.observed[indices],
                mode="markers",
                marker={"symbol": "triangle-up", "size": 13, "color": "#d62728"},
                name="Alert",
            )
        )

    figure.add_vline(
        x=config.change_day,
        line_dash="dash",
        line_color="#2ca02c",
        annotation_text="True change day",
    )
    if detection.first_post_change_alert is not None:
        figure.add_vline(
            x=detection.first_post_change_alert,
            line_dash="dashdot",
            line_color="#d62728",
            annotation_text="First detected alert",
        )

    figure.update_layout(
        title="Example synthetic trajectory",
        xaxis_title="Day",
        yaxis_title="Normalized voice measurement",
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.2},
        margin={"l": 50, "r": 35, "t": 65, "b": 85},
    )
    return figure
