# Longitudinal Voice Biomarker Sandbox

> **Status: working prototype.**  
> A small synthetic simulation sandbox for exploring how within-person
> variability, measurement noise, missing recordings, and alert settings may
> affect longitudinal voice monitoring.

## Why

Much of longitudinal vocal biomarker work focuses on differences between
clinical groups and on identifying useful speech tasks and features.

However, a voice measurement that distinguishes groups is not automatically
useful for monitoring one person over time.

In a longitudinal setting, an observed change may contain several components:

- natural day-to-day variation within the speaker;
- measurement variation caused by the recording and analysis process;
- a real change caused by the disease of interest.

A monitoring system also has to balance two competing goals:

- detecting a real change early;
- avoiding frequent false alerts during a stable period.

This project is a small simulation for making those assumptions and trade-offs
visible before working with real longitudinal data.

## Main question

Under a simplified synthetic setting:

> How do variability, measurement noise, missing recordings, and alert settings
> affect the ability to detect a change in one voice measurement over time?

## Main idea

The project simulates:

- one hypothetical participant;
- one normalized voice measurement;
- one scheduled measurement per day;
- an initial stable baseline period;
- one abrupt or gradual underlying change;
- occasional missing recordings;
- one transparent threshold-based alert rule.

The same configuration is then simulated repeatedly to estimate how often the
alert rule detects the change, misses it, or raises an alert too early.

## Simulation model

For day $t$, the observed value is generated as:

$$
y_t = \Delta_t + b_t + e_t
$$

where:

- $y_t$ is the observed synthetic voice measurement;
- $\Delta_t$ is the simulated underlying change;
- $b_t$ is natural within-person day-to-day variability;
- $e_t$ is measurement noise.

For the first version:

$$
b_t \sim \mathcal{N}(0, \sigma_{\mathrm{within}}^2)
$$

$$
e_t \sim \mathcal{N}(0, \sigma_{\mathrm{measurement}}^2)
$$

### Change patterns

Two simple change patterns are included.

**Abrupt change**

The underlying value remains stable until the selected change day and then
immediately moves by the configured magnitude.

**Gradual change**

The underlying value begins changing on the selected day, reaches the
configured magnitude linearly over seven days, and then remains at that level.

The gradual transition duration is fixed in this version.

## Simulation settings

The interface exposes the following parameters:

| Parameter | Description | Default |
|---|---|---:|
| Monitoring days | Length of the simulated monitoring period | 60 |
| Baseline days | Initial days used to estimate the personal baseline | 14 |
| Change day | Day on which the underlying change begins | 30 |
| Change magnitude | Size of the synthetic change | 1.5 |
| Change direction | Increase or decrease | Increase |
| Change type | Abrupt or gradual | Gradual |
| Within-person variability | Standard deviation of day-to-day variation | 0.5 |
| Measurement noise | Standard deviation of measurement variation | 0.3 |
| Missing probability | Probability that a scheduled recording is missing | 0.10 |
| Alert threshold | Distance from the baseline in estimated baseline SDs | 2.0 |
| Confirmations required | Consecutive threshold exceedances required for an alert | 2 |
| Simulations | Number of Monte Carlo runs | 500 |
| Random seed | Seed used to reproduce the simulation | 0 |

The change day must occur after the baseline period. The combined simulated
variability must also be greater than zero.

## Baseline and alert rule

The detector estimates a personal baseline from the available observations
during the initial baseline period:

$$
\hat{\mu}_{\mathrm{baseline}}
$$

and:

$$
\hat{\sigma}_{\mathrm{baseline}}
$$

Each later observation is standardized relative to that estimated baseline:

$$
z_t = \frac{y_t-\hat{\mu}_{\mathrm{baseline}}}
{\hat{\sigma}_{\mathrm{baseline}}}
$$

For a simulated increase, an observation exceeds the threshold when:

$$
z_t > k
$$

For a simulated decrease:

$$
z_t < -k
$$

where $k$ is the selected alert threshold.

An alert is only raised after the required number of consecutive threshold
exceedances. A missing observation or an observation within the threshold
breaks the sequence.

If fewer than five valid observations are available during the baseline period,
that simulation is marked as not evaluable.

## Outputs

### Example trajectory

One synthetic trajectory is plotted with:

- observed measurements;
- missing observations;
- the estimated baseline;
- the alert threshold;
- the true change day;
- the simulated underlying change;
- the first detected alert.

The corresponding summary reports:

```text
True change day
First post-change alert
Detection delay
False alert before change
```

If no post-change alert occurs before the end of monitoring, the change is
marked as missed.

### Repeated simulation

The same configuration is run repeatedly with newly sampled variation,
measurement noise, and missing observations.

The summary includes:

| Output | Meaning |
|---|---|
| Evaluable runs | Simulations with enough baseline observations |
| Detection probability | Proportion with an alert after the true change |
| Missed-change rate | Proportion with no alert after the true change |
| False-alert probability | Proportion with at least one alert before the true change |
| Median detection delay | Median days between the true change and first later alert |
| Detection-delay IQR | Variation in detection delay among detected runs |

## Interface

The interface is a single local Gradio page. The left side contains the
simulation settings. The right side shows:

1. one example longitudinal trajectory;
2. the repeated-simulation summary;
3. download options for the example trajectory and summary.

Exports:

```text
example_trajectory.csv
simulation_summary.json
```

## Setup and run

Python 3.11 or later is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python app/app.py
```

Install the development dependencies and run the checks with:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

## Implementation

```text
src/voice_monitoring_sandbox/
├── __init__.py    # public package interface
├── config.py      # configuration and input validation
├── simulation.py  # synthetic trajectory generation
├── detection.py   # baseline estimation and alert rule
├── evaluation.py  # repeated simulation and summary metrics
├── plotting.py    # trajectory visualization
└── pipeline.py    # end-to-end orchestration and exports
app/
└── app.py         # Gradio interface
tests/
├── test_simulation.py
├── test_detection.py
└── test_evaluation.py
```

The core functions are:

```python
simulate_trajectory(config, rng)
detect_change(trajectory, config)
evaluate_simulations(config, rng)
plot_trajectory(result)
```

The random-number generator is passed explicitly so that the same configuration
and seed produce the same result.

## Tests

- reproducibility with a fixed random seed;
- validation that the change occurs after the baseline period;
- detection of a large change under low-noise conditions;
- confirmation requirements for an alert;
- interruption of confirmation by missing observations;
- correct handling of positive and negative changes;
- non-negative detection delays;
- insufficient baseline observations;
- Monte Carlo probabilities remaining between zero and one.

## Current progress

- [x] Define the methodological question
- [x] Limit the first-version scope
- [x] Specify the simulation model
- [x] Specify the alert rule and evaluation outputs
- [x] Implement configuration validation
- [x] Implement synthetic trajectory generation
- [x] Implement change detection
- [x] Implement repeated simulation
- [x] Add visualization and exports
- [x] Add the Gradio interface
- [x] Add tests and automated checks

## Intended takeaway

This project is not a clinical monitoring system. It is a small methodological
sandbox built around one idea:

> Before interpreting a longitudinal change in a voice measurement as a
> health-related change, it is necessary to understand how the alert interacts
> with natural variability, measurement noise, missing observations, and the
> chosen decision threshold.
