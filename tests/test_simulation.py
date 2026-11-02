import random
import tempfile
import unittest
from pathlib import Path

from simulation import (
    ExperimentConfig,
    build_comparison_table,
    collect_metrics,
    power_of_two_choices,
    random_assignment,
    run_simulations,
    theoretical_baselines,
    write_latex_tables,
)


class AllocationTests(unittest.TestCase):
    def test_random_assignment_preserves_job_count(self):
        loads = random_assignment(servers=8, jobs=137, rng=random.Random(10))
        self.assertEqual(len(loads), 8)
        self.assertEqual(sum(loads), 137)
        self.assertTrue(all(load >= 0 for load in loads))

    def test_two_choices_preserves_job_count(self):
        loads = power_of_two_choices(servers=8, jobs=137, rng=random.Random(10))
        self.assertEqual(len(loads), 8)
        self.assertEqual(sum(loads), 137)
        self.assertTrue(all(load >= 0 for load in loads))

    def test_single_server_configuration(self):
        self.assertEqual(
            random_assignment(1, 25, random.Random(1)),
            [25],
        )
        self.assertEqual(
            power_of_two_choices(1, 25, random.Random(1)),
            [25],
        )

    def test_zero_jobs(self):
        self.assertEqual(random_assignment(4, 0, random.Random(2)), [0, 0, 0, 0])
        self.assertEqual(power_of_two_choices(4, 0, random.Random(2)), [0, 0, 0, 0])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            random_assignment(0, 10, random.Random(1))
        with self.assertRaises(ValueError):
            power_of_two_choices(4, -1, random.Random(1))

    def test_metrics(self):
        metrics = collect_metrics([1, 2, 3, 4], threshold=3)
        self.assertEqual(metrics["max_load"], 4)
        self.assertEqual(metrics["average_load"], 2.5)
        self.assertEqual(metrics["overloaded_servers"], 2)
        self.assertEqual(metrics["overload_percentage"], 50.0)


    def test_comparison_table_calculates_improvement(self):
        _, summary, _ = run_simulations(trials=2, base_seed=7)
        comparison = build_comparison_table(summary)
        self.assertEqual(len(comparison), 4)
        self.assertIn("max_load_improvement_pct", comparison.columns)
        self.assertTrue((comparison["max_load_improvement_pct"] >= 0).all())

    def test_theoretical_baselines_are_valid_probabilities(self):
        baselines = theoretical_baselines(
            [ExperimentConfig("test", servers=10, jobs=100)]
        )
        bound = baselines.loc[0, "chernoff_max_load_union_upper_bound"]
        self.assertGreaterEqual(bound, 0.0)
        self.assertLessEqual(bound, 1.0)


    def test_latex_tables_are_generated(self):
        _, summary, _ = run_simulations(trials=2, base_seed=9)
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "latex_tables.tex"
            write_latex_tables(summary, output_path)
            self.assertTrue(output_path.is_file())
            contents = output_path.read_text(encoding="utf-8")
            self.assertEqual(contents.count(r"\begin{table}"), 3)
            self.assertIn("Improvement", contents)

    def test_experiment_is_reproducible(self):
        first_trials, first_summary, _ = run_simulations(trials=3, base_seed=42)
        second_trials, second_summary, _ = run_simulations(trials=3, base_seed=42)
        self.assertTrue(first_trials.equals(second_trials))
        self.assertTrue(first_summary.equals(second_summary))


if __name__ == "__main__":
    unittest.main()
