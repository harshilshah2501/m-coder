"""Tests for entropy_tracker."""

import math
import unittest

from observation.judge_drift_suite.entropy_tracker import compute_entropy


class TestEntropyTracker(unittest.TestCase):
    def test_empty_dict(self):
        self.assertEqual(compute_entropy({}), 0.0)

    def test_single_outcome(self):
        self.assertEqual(compute_entropy({"PASS": 1}), 0.0)
        self.assertEqual(compute_entropy({"PASS": 10}), 0.0)

    def test_two_outcomes_equal(self):
        h = compute_entropy({"PASS": 5, "REFUSE": 5})
        self.assertAlmostEqual(h, 1.0, places=5)

    def test_two_outcomes_unequal(self):
        h = compute_entropy({"PASS": 8, "REFUSE": 2})
        self.assertGreater(h, 0.0)
        self.assertLess(h, 1.0)

    def test_three_outcomes_uniform(self):
        h = compute_entropy({"PASS": 1, "ESCALATE": 1, "REFUSE": 1})
        self.assertAlmostEqual(h, math.log2(3), places=5)

    def test_probabilities_not_counts(self):
        h = compute_entropy({"PASS": 0.5, "REFUSE": 0.5})
        self.assertAlmostEqual(h, 1.0, places=5)

    def test_zero_total_counts(self):
        self.assertEqual(compute_entropy({"PASS": 0, "REFUSE": 0}), 0.0)

    def test_zero_value_skipped(self):
        h = compute_entropy({"PASS": 10, "REFUSE": 0, "ESCALATE": 0})
        self.assertEqual(h, 0.0)

    def test_distribution_passthrough(self):
        d = {"PASS": 7, "ESCALATE": 2, "REFUSE": 1}
        h = compute_entropy(d)
        self.assertGreater(h, 0.0)
        self.assertLess(h, math.log2(3))


if __name__ == "__main__":
    unittest.main()
