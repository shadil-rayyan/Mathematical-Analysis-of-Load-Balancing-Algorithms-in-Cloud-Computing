# Probabilistic Load Balancing in Cloud Computing

A reproducible Python simulation comparing **Random Assignment** with the **Power of Two Choices** algorithm using the balls-and-bins model.

**Recommended GitHub repository name:** `probabilistic-cloud-load-balancing`

## 1. Project overview

The simulation models `m` equal-sized jobs arriving at `n` identical servers.

- **Random Assignment:** each job is assigned to one uniformly selected server.
- **Power of Two Choices:** two servers are sampled independently and uniformly; the job is assigned to the less-loaded server. If their loads are equal, the choice is made randomly.

The two choices are sampled **with replacement**, so both samples may identify the same server. This matches the independent sampling assumption in the report.

The project evaluates four configurations:

| Experiment | Servers (`n`) | Jobs (`m`) | Average load (`m/n`) | Overload threshold |
|---|---:|---:|---:|---:|
| 1 | 50 | 500 | 10 | 12 |
| 2 | 100 | 1,000 | 10 | 12 |
| 3 | 500 | 5,000 | 10 | 12 |
| 4 | 100 | 10,000 | 100 | 120 |

Each configuration is repeated for 30 independent trials by default. The base random seed is `42`.

## 2. Repository structure

```text
probabilistic-cloud-load-balancing/
├── AGENTS.md
├── README.md
├── .gitignore
├── requirements.txt
├── simulation.py
├── tests/
│   └── test_simulation.py
└── results/
    ├── results.csv
    ├── comparison_results.csv
    ├── latex_tables.tex
    ├── trial_results.csv
    ├── theoretical_baselines.csv
    ├── maximum_load.png
    ├── load_distribution.png
    └── overload_comparison.png
```

## 3. Setup

Python 3.10 or newer is recommended.

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Run the experiments

From the repository root:

```bash
python simulation.py
```

Optional settings:

```bash
python simulation.py --trials 30 --seed 42 --output-dir results
```

The run prints a compact summary and creates or replaces the following files in the output directory:

| File | Contents |
|---|---|
| `results.csv` | Mean and sample standard deviation of each metric across trials, grouped by experiment and algorithm. |
| `comparison_results.csv` | One row per configuration, with both algorithms side by side and maximum-load improvement percentage already calculated. |
| `latex_tables.tex` | Ready-to-paste LaTeX table environments containing means and between-trial sample standard deviations. |
| `trial_results.csv` | One row per algorithm, configuration, and individual trial. |
| `theoretical_baselines.csv` | Expected load, binomial variance, and Chernoff upper bounds for random assignment. |
| `maximum_load.png` | Mean maximum server load, with error bars showing between-trial standard deviation. |
| `load_distribution.png` | Histograms of server loads across trials for each configuration. |
| `overload_comparison.png` | Mean number of overloaded servers, with between-trial standard deviation. |

The simulation is deterministic for a fixed set of arguments. Independent seeds are derived from the base seed, configuration index, trial index, and algorithm index.

## 5. Metrics and definitions

The overload threshold is defined as:

\[
T = \lceil 1.2(m/n) \rceil.
\]

A server is counted as overloaded when its load is **greater than or equal to** `T`.

For every trial, the program calculates:

- `max_load`: highest number of jobs assigned to any server.
- `average_load`: mean number of jobs per server (equal to `m/n`).
- `load_std_dev`: population standard deviation across the server loads in that trial.
- `overloaded_servers`: number of servers whose load is at least `T`.
- `overload_percentage`: overloaded servers divided by total servers, multiplied by 100.

In `results.csv`, each metric is summarized by its mean and sample standard deviation across independent trials. For example, `load_std_dev_mean` is the average of the per-trial workload standard deviations; `load_std_dev_std` describes how that per-trial metric varies between trials.

## 6. Mathematical baseline

For random assignment, the load of a fixed server follows:

\[
L_i \sim \operatorname{Binomial}(m,1/n),\qquad
E[L_i]=m/n=\lambda,
\]

\[
\operatorname{Var}(L_i)=\lambda(1-1/n).
\]

The `theoretical_baselines.csv` file applies the Chernoff upper-tail inequality to the integer overload threshold. It also applies a union bound across all servers to bound the probability that at least one server reaches the threshold. The bound is capped at 1 because probabilities cannot exceed 1.

**Important:** these Chernoff calculations are for the independent one-choice/random-assignment model. They are not a theoretical bound for Power of Two Choices. The classical asymptotic maximum-load results commonly quoted for the two algorithms use the special setting `m=n`; the four experiments in this repository use `m=10n` or `m=100n`, so those asymptotic expressions should not be presented as exact predictions for these finite experiments.

## 7. Run the tests

```bash
python -m unittest discover -s tests -v
```

The tests check load conservation, valid edge cases, metric calculations, input validation, and reproducibility.

## 8. Use the generated results in the LaTeX report

1. Run `python simulation.py` from the project root.
2. Open `results/latex_tables.tex`. It contains three ready-to-paste table environments with means and between-trial standard deviations. Paste them over the corresponding placeholder tables in the report. The maximum-load table includes the improvement percentage.
3. The side-by-side values are also available in `results/comparison_results.csv`; use `results/results.csv` for each algorithm's separate metrics.
4. Replace the placeholder figure boxes with the PNG files. The LaTeX source already looks for these exact names:
   - `maximum_load.png`
   - `load_distribution.png`
   - `overload_comparison.png`
5. For consistent figure paths, copy the three PNG files from `results/` into the directory containing the `.tex` file, or update the `\includegraphics` paths to `results/<filename>`.
6. State the number of trials, base seed, and threshold definition in the report. Do not describe simulation output as a real cloud deployment measurement; it is evidence from this model and its assumptions.

For the improvement percentage in the report, calculate it from the **mean** maximum loads:

\[
I=\frac{\overline{L}_{\max,\,random}-\overline{L}_{\max,\,two}}{\overline{L}_{\max,\,random}}\times100\%.
\]

## 9. Limitations

This is a discrete-event allocation simulation, not a production cloud benchmark. It assumes identical servers, equal-sized jobs, immediate load visibility, no job completion, no network latency, and no server failures. The results should be interpreted within these assumptions.

## 10. Suggested GitHub workflow

```bash
git init
git add .
git commit -m "Add reproducible probabilistic load balancing simulation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/probabilistic-cloud-load-balancing.git
git push -u origin main
```

Create the repository on GitHub with the name `probabilistic-cloud-load-balancing`. Do not initialize it with a second README if you are pushing this local repository as-is.
