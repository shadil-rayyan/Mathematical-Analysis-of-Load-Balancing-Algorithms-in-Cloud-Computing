# AGENTS.md — Project Instructions for Coding Agents

These instructions apply to the entire `probabilistic-cloud-load-balancing` repository.

## 1. Project purpose

Maintain a reproducible educational research simulation comparing:

1. Uniform random assignment of jobs to servers.
2. The Power of Two Choices allocation strategy.

The model is the classical balls-and-bins abstraction. A job is a ball, a server is a bin, and the number of jobs assigned to a server is its load. This repository is a simulation and teaching/research artifact; it is not a production cloud load balancer.

## 2. Source of truth

- `simulation.py` is the source of truth for allocation logic, experiment configurations, metrics, reproducibility, CSV exports, and plot generation.
- `tests/test_simulation.py` contains automated correctness and reproducibility checks.
- `README.md` documents setup, execution, model assumptions, and generated outputs.
- The LaTeX report supplied by the project owner is an external report artifact. Do not silently change its claims or references while changing the Python implementation.

When code and documentation disagree, inspect the implementation and tests, decide which behaviour is intended, then update both code and documentation in the same change.

## 3. Mathematical and modelling requirements

### Random Assignment

For each arriving job, select exactly one server uniformly at random. The server load for a fixed server follows a Binomial distribution with parameters `m` and `1/n`:

\[
L_i\sim\operatorname{Binomial}(m,1/n),\quad
E[L_i]=m/n,\quad
\operatorname{Var}(L_i)=(m/n)(1-1/n).
\]

### Power of Two Choices

For each arriving job:

1. Sample two server indices independently and uniformly **with replacement**.
2. Compare their current loads.
3. Select a server with the smaller load.
4. If the loads tie, choose uniformly between the two sampled positions.
5. Increment exactly one server's load by one.

Do not silently switch to sampling without replacement. If the sampling model is intentionally changed, update the README, mathematical description, tests, and report guidance.

### Workload conservation

For either algorithm, after assigning `m` jobs to `n` servers:

- There must be exactly `n` non-negative integer loads.
- The sum of the loads must equal `m`.
- Each job must increment exactly one server.

The simulation currently checks the total-load invariant after every trial. Preserve this check.

### Overload definition

Use:

\[
T=\lceil1.2(m/n)\rceil.
\]

A server is overloaded when its load is greater than or equal to `T`. Keep the `>=` comparison consistent in code, tests, README, CSV interpretation, and report instructions.

### Chernoff bound scope

The binomial Chernoff bound and its union-bound extension in `theoretical_baselines.csv` apply to the one-choice/random-assignment model. Do not present those bounds as directly proving an overload probability for Power of Two Choices.

The classical asymptotic maximum-load formulas for `m=n` are not exact finite-size predictions for this repository's experiments (`m=10n` and `m=100n`). Keep this distinction explicit in documentation and generated analyses.

## 4. Experiment defaults

Unless the project owner explicitly requests a change, preserve these defaults:

| Experiment | Servers | Jobs |
|---|---:|---:|
| Experiment 1 | 50 | 500 |
| Experiment 2 | 100 | 1,000 |
| Experiment 3 | 500 | 5,000 |
| Experiment 4 | 100 | 10,000 |

Default run settings:

- 30 independent trials per experiment and algorithm.
- Base random seed: `42`.
- Equal-sized jobs.
- Identical servers.
- No job completion, failures, queueing, or network-delay model.

A fixed base seed must reproduce the same trial-level results on the same supported software environment. Derive seeds deterministically; do not use Python's built-in `hash()` for seed derivation because hash randomization can vary between processes.

## 5. Metrics and aggregation

Preserve the following per-trial metrics unless an explicit research change is requested:

- Maximum server load.
- Mean server load.
- Population standard deviation across server loads within a trial (`ddof=0`).
- Number of overloaded servers.
- Percentage of overloaded servers.

When aggregating results across independent trials:

- Report the arithmetic mean for each per-trial metric.
- Report the sample standard deviation across trials (`ddof=1`).
- Use clear column names that distinguish within-trial spread from between-trial variation.

Do not confuse the mean of per-trial server-load standard deviations with one pooled standard deviation over all servers and all trials.

## 6. Engineering standards

- Use Python 3.10+ syntax and standard type annotations.
- Keep allocation logic in small, independently testable functions.
- Use `random.Random` instances passed into functions; do not rely on module-global random state.
- Validate public function inputs and raise clear `ValueError` exceptions for invalid counts.
- Avoid unnecessary dependencies. If a dependency is added, update `requirements.txt` and explain why in `README.md`.
- Use deterministic output ordering for CSV files and plots.
- Write generated files only to the requested output directory.
- Do not make network calls during simulation or tests.
- Use clear names and comments for assumptions that affect the mathematical model.

## 7. Required validation before completing a code change

Run these commands from the repository root:

```bash
python -m unittest discover -s tests -v
python simulation.py
```

When changing random allocation, metrics, output formats, or plots, also inspect the generated files under `results/` and verify:

1. `results.csv` has one summary row per experiment and algorithm.
2. `trial_results.csv` has one row per trial, experiment, and algorithm.
3. `comparison_results.csv` has one row per workload configuration and calculates maximum-load improvement from the mean loads.
4. `latex_tables.tex` contains three LaTeX table environments with trial means and between-trial sample standard deviations.
5. `theoretical_baselines.csv` contains only random-assignment binomial/Chernoff calculations.
6. The three PNG files exist and are not empty.
7. Every trial assigns exactly the configured number of jobs.
8. Re-running with the same arguments produces identical CSV data (plot metadata may differ by library version).

If a command cannot be run, state that clearly; do not claim the tests or simulation passed.

## 8. Report and scientific-integrity requirements

- Never invent experimental results, citations, DOI details, or claims about real cloud performance.
- Keep simulated observations separate from mathematical guarantees and published asymptotic results.
- When reporting a number, identify whether it is a theoretical value, a single-trial observation, or an average over trials.
- Include the run settings (trial count, seed, workload sizes, and overload threshold) when presenting results.
- Do not describe the experiment as a live cloud deployment or production benchmark.
- Preserve source attribution and verify bibliography details before editing references.

## 9. Change-management checklist

Before finishing a change:

1. Identify whether it changes the probability model, algorithm, metric, configuration, output schema, or only presentation.
2. Update affected code and tests together.
3. Update `README.md` and this file when documented behaviour changes.
4. Regenerate results and plots if the simulation behaviour or defaults change.
5. Run the validation commands in Section 7.
6. Summarize files changed, tests run, outputs regenerated, and any remaining limitations.

Do not make unrelated refactors that obscure the research logic.
