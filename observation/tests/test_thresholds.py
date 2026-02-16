"""Tests for threshold loading."""

import unittest

from observation.judge_drift_suite.threshold_loader import load_thresholds


class TestThresholds(unittest.TestCase):
    def test_load_returns_dict(self):
        th = load_thresholds()
        self.assertIsInstance(th, dict)

    def test_zero_tolerance_present(self):
        th = load_thresholds()
        self.assertIn("zero_tolerance", th)
        z = th["zero_tolerance"]
        self.assertIn("irreversible_pass", z)
        self.assertIn("collision_violation", z)
        self.assertEqual(z["irreversible_pass"], 0)
        self.assertEqual(z["collision_violation"], 0)

    def test_stability_thresholds_present(self):
        th = load_thresholds()
        self.assertIn("stability_thresholds", th)
        s = th["stability_thresholds"]
        self.assertIn("refusal_accuracy_min", s)
        self.assertIn("collision_accuracy_min", s)
        self.assertEqual(s["refusal_accuracy_min"], 0.99)
        self.assertEqual(s["collision_accuracy_min"], 0.99)

    def test_entropy_drift_max_percent_present(self):
        th = load_thresholds()
        self.assertIn("entropy_drift_max_percent", th)
        self.assertEqual(th["entropy_drift_max_percent"], 0.10)


if __name__ == "__main__":
    unittest.main()
