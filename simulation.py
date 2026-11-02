"""Reproducible simulation of randomized cloud load-balancing strategies.

The project compares:
1. Random assignment: each job chooses one server uniformly at random.
2. Power of Two Choices: each job samples two servers independently (with
   replacement) and chooses the currently less-loaded server. Ties are broken
   uniformly between the two sampled choices.

Run from the repository root:
    python simulation.py

Optional arguments:
    python simulation.py --trials 30 --seed 42 --output-dir results
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExperimentConfig:
    """One fixed server/job workload configuration."""

    experiment: str
    servers: int
    jobs: int

    @property
    def average_load(self) -> float:
        return self.jobs / self.servers

    @property
    def overload_threshold(self) -> int:
        # A server is overloaded when its load is >= this threshold.
        return int(np.ceil(1.2 * self.average_load))


DEFAULT_CONFIGS: tuple[ExperimentConfig, ...] = (
    ExperimentConfig("Experiment 1", servers=50, jobs=500),
    ExperimentConfig("Experiment 2", servers=100, jobs=1_000),
    ExperimentConfig("Experiment 3", servers=500, jobs=5_000),
    ExperimentConfig("Experiment 4", servers=100, jobs=10_000),
)

ALGORITHMS = ("Random Assignment", "Power of Two Choices")


def validate_problem_size(servers: int, jobs: int) -> None:
    """Reject invalid server/job counts with a helpful error."""
    if not isinstance(servers, int) or isinstance(servers, bool) or servers < 1:
        raise ValueError("servers must be a positive integer")
    if not isinstance(jobs, int) or isinstance(jobs, bool) or jobs < 0:
        raise ValueError("jobs must be a non-negative integer")


def random_assignment(servers: int, jobs: int, rng: random.Random) -> list[int]:
    """Assign each job to one uniformly selected server."""
    validate_problem_size(servers, jobs)
    loads = [0] * servers

    for _ in range(jobs):
        selected = rng.randrange(servers)
        loads[selected] += 1

    return loads


def power_of_two_choices(servers: int, jobs: int, rng: random.Random) -> list[int]:
    """Assign each job to the less-loaded of two random server choices.

    The two choices are sampled independently with replacement, matching the
    wording of the mathematical model. Consequently, both samples may refer
    to the same server. If the sampled servers have equal loads, the tie is
    broken uniformly between the two sampled positions.
    """
    validate_problem_size(servers, jobs)
    loads = [0] * servers

    for _ in range(jobs):
        first = rng.randrange(servers)
        second = rng.randrange(servers)

        if loads[first] < loads[second]:
            selected = first
        elif loads[second] < loads[first]:
            selected = second
        else:
            selected = (first, second)[rng.randrange(2)]

        loads[selected] += 1

    return loads


def collect_metrics(loads: Iterable[int], threshold: int) -> dict[str, float | int]:
    """Calculate the metrics for one completed trial."""
    load_array = np.asarray(list(loads), dtype=np.int64)
    if load_array.ndim != 1 or load_array.size == 0:
        raise ValueError("loads must contain at least one server load")
    if np.any(load_array < 0):
        raise ValueError("server loads cannot be negative")

    overloaded = int(np.count_nonzero(load_array >= threshold))
    server_count = int(load_array.size)

    return {
        "max_load": int(load_array.max()),
        "average_load": float(load_array.mean()),
        # Population SD across servers within this individual trial.
        "load_std_dev": float(load_array.std(ddof=0)),
        "overloaded_servers": overloaded,
        "overload_percentage": 100.0 * overloaded / server_count,
    }


def _trial_seed(base_seed: int, config_index: int, trial_index: int, algorithm_index: int) -> int:
    """Create deterministic, separate RNG seeds without using Python hash()."""
    return base_seed + config_index * 1_000_000 + trial_index * 10 + algorithm_index


def run_simulations(
    configs: Iterable[ExperimentConfig] = DEFAULT_CONFIGS,
    trials: int = 30,
    base_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[tuple[str, str], list[int]]]:
    """Run all configurations and return trial rows, summary rows, load samples.

    The summary's *_mean fields average the metric over independent trials.
    The corresponding *_sd fields are sample standard deviations (ddof=1)
    across trials. `load_std_dev` itself is first calculated across servers
    inside each trial, then summarized across trials.
    """
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 1:
        raise ValueError("trials must be a positive integer")
    if not isinstance(base_seed, int) or isinstance(base_seed, bool):
        raise ValueError("base_seed must be an integer")

    config_list = tuple(configs)
    if not config_list:
        raise ValueError("at least one experiment configuration is required")
    for config in config_list:
        validate_problem_size(config.servers, config.jobs)

    algorithms: tuple[Callable[[int, int, random.Random], list[int]], ...] = (
        random_assignment,
        power_of_two_choices,
    )
    trial_rows: list[dict[str, object]] = []
    load_samples: dict[tuple[str, str], list[int]] = {
        (config.experiment, algorithm_name): []
        for config in config_list
        for algorithm_name in ALGORITHMS
    }

    for config_index, config in enumerate(config_list):
        threshold = config.overload_threshold

        for trial_index in range(trials):
            for algorithm_index, (algorithm_name, algorithm) in enumerate(
                zip(ALGORITHMS, algorithms)
            ):
                seed = _trial_seed(base_seed, config_index, trial_index, algorithm_index)
                rng = random.Random(seed)
                loads = algorithm(config.servers, config.jobs, rng)
                metrics = collect_metrics(loads, threshold)

                # A guard against accidental changes that violate the model.
                if sum(loads) != config.jobs:
                    raise RuntimeError(
                        f"{algorithm_name} assigned {sum(loads)} jobs; "
                        f"expected {config.jobs}"
                    )

                load_samples[(config.experiment, algorithm_name)].extend(loads)
                trial_rows.append(
                    {
                        "experiment": config.experiment,
                        "servers": config.servers,
                        "jobs": config.jobs,
                        "average_load": config.average_load,
                        "overload_threshold": threshold,
                        "trial": trial_index + 1,
                        "seed": seed,
                        "algorithm": algorithm_name,
                        **metrics,
                    }
                )

    trial_df = pd.DataFrame(trial_rows)
    group_columns = [
        "experiment",
        "servers",
        "jobs",
        "average_load",
        "overload_threshold",
        "algorithm",
    ]
    metric_columns = [
        "max_load",
        "load_std_dev",
        "overloaded_servers",
        "overload_percentage",
    ]
    summary = (
        trial_df.groupby(group_columns, sort=False)[metric_columns]
        .agg(["mean", "std"])
        .reset_index()
    )
    summary.columns = [
        "_".join(str(part) for part in column if part).rstrip("_")
        if isinstance(column, tuple)
        else str(column)
        for column in summary.columns
    ]
    summary["trials"] = trials

    # Make the output order predictable and the CSV easy to read.
    summary = summary[
        group_columns
        + [
            "trials",
            "max_load_mean",
            "max_load_std",
            "load_std_dev_mean",
            "load_std_dev_std",
            "overloaded_servers_mean",
            "overloaded_servers_std",
            "overload_percentage_mean",
            "overload_percentage_std",
        ]
    ]

    return trial_df, summary, load_samples


def _plot_maximum_load(summary: pd.DataFrame, output_path: Path) -> None:
    experiments = list(summary["experiment"].drop_duplicates())
    x = np.arange(len(experiments), dtype=float)
    width = 0.36

    fig, ax = plt.subplots(figsize=(10, 6))
    for offset, algorithm in zip((-width / 2, width / 2), ALGORITHMS):
        subset = (
            summary[summary["algorithm"] == algorithm]
            .set_index("experiment")
            .reindex(experiments)
        )
        ax.bar(
            x + offset,
            subset["max_load_mean"],
            width,
            yerr=subset["max_load_std"].fillna(0),
            capsize=4,
            label=algorithm,
        )

    ax.set_title("Mean Maximum Server Load Across Trials")
    ax.set_xlabel("Workload configuration")
    ax.set_ylabel("Maximum jobs on a server")
    ax.set_xticks(x, experiments)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def _plot_load_distribution(
    configs: Iterable[ExperimentConfig],
    load_samples: dict[tuple[str, str], list[int]],
    output_path: Path,
) -> None:
    config_list = tuple(configs)
    if not config_list:
        raise ValueError("at least one experiment configuration is required for plotting")
    columns = min(2, len(config_list))
    rows = int(np.ceil(len(config_list) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(6 * columns, 4 * rows), squeeze=False)
    axes_flat = axes.flat

    for ax, config in zip(axes_flat, config_list):
        random_loads = load_samples[(config.experiment, ALGORITHMS[0])]
        two_choice_loads = load_samples[(config.experiment, ALGORITHMS[1])]
        largest = max(max(random_loads), max(two_choice_loads))
        bins = np.arange(-0.5, largest + 1.5, 1)

        ax.hist(random_loads, bins=bins, alpha=0.55, label=ALGORITHMS[0])
        ax.hist(two_choice_loads, bins=bins, alpha=0.55, label=ALGORITHMS[1])
        ax.set_title(
            f"{config.experiment}: n={config.servers}, m={config.jobs}"
        )
        ax.set_xlabel("Jobs assigned to a server")
        ax.set_ylabel("Server observations across trials")
        ax.grid(axis="y", alpha=0.2)
        ax.legend(fontsize="small")

    # Hide unused axes if a caller supplies fewer than four configurations.
    for ax in list(axes.flat)[len(config_list) :]:
        ax.set_visible(False)

    fig.suptitle("Server Load Distributions Across Independent Trials", y=1.01)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _plot_overload(summary: pd.DataFrame, output_path: Path) -> None:
    experiments = list(summary["experiment"].drop_duplicates())
    x = np.arange(len(experiments), dtype=float)
    width = 0.36

    fig, ax = plt.subplots(figsize=(10, 6))
    for offset, algorithm in zip((-width / 2, width / 2), ALGORITHMS):
        subset = (
            summary[summary["algorithm"] == algorithm]
            .set_index("experiment")
            .reindex(experiments)
        )
        ax.bar(
            x + offset,
            subset["overloaded_servers_mean"],
            width,
            yerr=subset["overloaded_servers_std"].fillna(0),
            capsize=4,
            label=algorithm,
        )

    ax.set_title("Mean Number of Overloaded Servers Across Trials")
    ax.set_xlabel("Workload configuration")
    ax.set_ylabel("Overloaded servers (load >= threshold)")
    ax.set_xticks(x, experiments)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def generate_plots(
    summary: pd.DataFrame,
    configs: Iterable[ExperimentConfig],
    load_samples: dict[tuple[str, str], list[int]],
    output_dir: Path,
) -> None:
    """Generate the three figures referenced by the LaTeX report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    _plot_maximum_load(summary, output_dir / "maximum_load.png")
    _plot_load_distribution(configs, load_samples, output_dir / "load_distribution.png")
    _plot_overload(summary, output_dir / "overload_comparison.png")


def build_comparison_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Create one wide row per configuration for easy LaTeX table entry."""
    keys = [
        "experiment",
        "servers",
        "jobs",
        "average_load",
        "overload_threshold",
    ]
    metric_columns = [
        "max_load_mean",
        "max_load_std",
        "load_std_dev_mean",
        "load_std_dev_std",
        "overloaded_servers_mean",
        "overloaded_servers_std",
        "overload_percentage_mean",
        "overload_percentage_std",
    ]

    random_rows = summary[summary["algorithm"] == ALGORITHMS[0]][keys + metric_columns]
    two_choice_rows = summary[summary["algorithm"] == ALGORITHMS[1]][keys + metric_columns]
    random_rows = random_rows.rename(
        columns={column: f"random_{column}" for column in metric_columns}
    )
    two_choice_rows = two_choice_rows.rename(
        columns={column: f"two_choices_{column}" for column in metric_columns}
    )
    comparison = random_rows.merge(two_choice_rows, on=keys, validate="one_to_one")

    random_max = comparison["random_max_load_mean"]
    comparison["max_load_improvement_pct"] = np.where(
        random_max > 0,
        (random_max - comparison["two_choices_max_load_mean"]) / random_max * 100.0,
        0.0,
    )
    return comparison


def theoretical_baselines(configs: Iterable[ExperimentConfig]) -> pd.DataFrame:
    """Calculate one-choice binomial moments and Chernoff overload bounds.

    For a fixed server under random assignment, L_i ~ Binomial(m, 1/n).
    The union-bound column bounds P(max_i L_i >= threshold). This bound is
    not a Power of Two Choices bound.
    """
    rows: list[dict[str, float | int | str]] = []
    for config in configs:
        mean = config.average_load
        variance = mean * (1.0 - 1.0 / config.servers)
        threshold = config.overload_threshold
        delta = threshold / mean - 1.0

        # P(L_i >= (1 + delta) * mean) <=
        # (e^delta / (1 + delta)^(1 + delta))^mean.
        log_single_bound = mean * (delta - (1.0 + delta) * math.log1p(delta))
        single_server_bound = math.exp(log_single_bound) if log_single_bound > -745 else 0.0
        union_bound = min(1.0, config.servers * single_server_bound)

        rows.append(
            {
                "experiment": config.experiment,
                "servers": config.servers,
                "jobs": config.jobs,
                "average_load": mean,
                "binomial_variance_per_server": variance,
                "binomial_std_dev_per_server": math.sqrt(variance),
                "overload_threshold": threshold,
                "chernoff_delta": delta,
                "chernoff_single_server_upper_bound": single_server_bound,
                "chernoff_max_load_union_upper_bound": union_bound,
            }
        )
    return pd.DataFrame(rows)


def write_latex_tables(summary: pd.DataFrame, output_path: Path) -> None:
    """Write ready-to-paste LaTeX tables with mean +/- between-trial SD."""
    comparison = build_comparison_table(summary)

    def mean_sd(mean: float, sd: float) -> str:
        return f"{mean:.2f} $\\pm$ {sd:.2f}"

    lines = [
        "% Generated by simulation.py. Values are means +/- sample SD across trials.",
        "% Copy these table environments into the Experiments and Results section.",
        "",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Mean maximum server load across independent trials}",
        r"\begin{tabular}{cccc}",
        r"\toprule",
        r"Experiment & Random Assignment & Two Choices & Improvement (\%) \\",
        r"\midrule",
    ]

    for _, row in comparison.iterrows():
        number = str(row["experiment"]).replace("Experiment ", "")
        lines.append(
            f"{number} & "
            f"{mean_sd(row['random_max_load_mean'], row['random_max_load_std'])} & "
            f"{mean_sd(row['two_choices_max_load_mean'], row['two_choices_max_load_std'])} & "
            f"{row['max_load_improvement_pct']:.2f} \\\\" 
        )

    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
            r"\begin{table}[H]",
            r"\centering",
            r"\caption{Mean standard deviation of server workloads across trials}",
            r"\begin{tabular}{ccc}",
            r"\toprule",
            r"Experiment & Random Assignment & Two Choices \\",
            r"\midrule",
        ]
    )
    for _, row in comparison.iterrows():
        number = str(row["experiment"]).replace("Experiment ", "")
        lines.append(
            f"{number} & "
            f"{mean_sd(row['random_load_std_dev_mean'], row['random_load_std_dev_std'])} & "
            f"{mean_sd(row['two_choices_load_std_dev_mean'], row['two_choices_load_std_dev_std'])} \\\\" 
        )

    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
            r"\begin{table}[H]",
            r"\centering",
            r"\caption{Mean number of overloaded servers across trials}",
            r"\begin{tabular}{ccc}",
            r"\toprule",
            r"Experiment & Random Assignment & Two Choices \\",
            r"\midrule",
        ]
    )
    for _, row in comparison.iterrows():
        number = str(row["experiment"]).replace("Experiment ", "")
        lines.append(
            f"{number} & "
            f"{mean_sd(row['random_overloaded_servers_mean'], row['random_overloaded_servers_std'])} & "
            f"{mean_sd(row['two_choices_overloaded_servers_mean'], row['two_choices_overloaded_servers_std'])} \\\\" 
        )

    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(summary: pd.DataFrame) -> None:
    """Print a compact table suitable for checking report values."""
    columns = [
        "experiment",
        "algorithm",
        "max_load_mean",
        "load_std_dev_mean",
        "overloaded_servers_mean",
        "overload_percentage_mean",
    ]
    display = summary[columns].copy()
    for column in columns[2:]:
        display[column] = display[column].map(lambda value: f"{value:.3f}")
    print("\nSUMMARY (means across independent trials)\n")
    print(display.to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare random assignment and Power of Two Choices."
    )
    parser.add_argument(
        "--trials", type=int, default=30,
        help="independent trials per configuration and algorithm (default: 30)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="base seed for deterministic random-number generation (default: 42)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results"),
        help="directory for CSV files and plots (default: results)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trial_df, summary, load_samples = run_simulations(
        configs=DEFAULT_CONFIGS,
        trials=args.trials,
        base_seed=args.seed,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trial_df.to_csv(args.output_dir / "trial_results.csv", index=False)
    summary.to_csv(args.output_dir / "results.csv", index=False)
    build_comparison_table(summary).to_csv(
        args.output_dir / "comparison_results.csv", index=False
    )
    write_latex_tables(summary, args.output_dir / "latex_tables.tex")
    theoretical_baselines(DEFAULT_CONFIGS).to_csv(
        args.output_dir / "theoretical_baselines.csv", index=False
    )
    generate_plots(summary, DEFAULT_CONFIGS, load_samples, args.output_dir)

    print_summary(summary)
    print(f"\nSaved summary CSV: {args.output_dir / 'results.csv'}")
    print(f"Saved comparison CSV: {args.output_dir / 'comparison_results.csv'}")
    print(f"Saved LaTeX tables: {args.output_dir / 'latex_tables.tex'}")
    print(f"Saved trial-level CSV: {args.output_dir / 'trial_results.csv'}")
    print(f"Saved theoretical baselines: {args.output_dir / 'theoretical_baselines.csv'}")
    print(f"Saved plots in: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
