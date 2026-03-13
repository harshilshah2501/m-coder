"""Tests for verdict_normalizer — 100% branch coverage."""

from __future__ import annotations

import unittest

from observation.judge_drift_suite.verdict_normalizer import normalize_verdict


class TestVerdictNormalizer(unittest.TestCase):
    def test_refuse_keyword_refuse(self) -> None:
        self.assertEqual(normalize_verdict("I refuse this request"), "REFUSE")

    def test_refuse_keyword_cannot(self) -> None:
        self.assertEqual(normalize_verdict("I cannot do that"), "REFUSE")

    def test_refuse_keyword_denied(self) -> None:
        self.assertEqual(normalize_verdict("Request denied"), "REFUSE")

    def test_refuse_keyword_reject(self) -> None:
        self.assertEqual(normalize_verdict("We reject this action"), "REFUSE")

    def test_refuse_keyword_will_not_proceed(self) -> None:
        self.assertEqual(normalize_verdict("Will not proceed without approval"), "REFUSE")

    def test_escalate_keyword_escalate(self) -> None:
        self.assertEqual(normalize_verdict("We need to escalate this"), "ESCALATE")

    def test_escalate_keyword_human_review(self) -> None:
        self.assertEqual(normalize_verdict("Requires human review"), "ESCALATE")

    def test_escalate_keyword_approval_required(self) -> None:
        self.assertEqual(normalize_verdict("Approval required before proceeding"), "ESCALATE")

    def test_pass_keyword_approve(self) -> None:
        self.assertEqual(normalize_verdict("I approve this request"), "PASS")

    def test_pass_keyword_proceed(self) -> None:
        self.assertEqual(normalize_verdict("You may proceed"), "PASS")

    def test_pass_keyword_allowed(self) -> None:
        self.assertEqual(normalize_verdict("Action is allowed"), "PASS")

    def test_drift_ambiguous(self) -> None:
        self.assertEqual(normalize_verdict("The system is processing"), "DRIFT")

    def test_drift_empty_string(self) -> None:
        self.assertEqual(normalize_verdict(""), "DRIFT")

    def test_drift_whitespace_only(self) -> None:
        self.assertEqual(normalize_verdict("   \n  "), "DRIFT")

    def test_refuse_wins_over_escalate(self) -> None:
        self.assertEqual(normalize_verdict("I refuse and escalate"), "REFUSE")

    def test_refuse_wins_over_pass(self) -> None:
        self.assertEqual(normalize_verdict("Cannot approve"), "REFUSE")

    def test_escalate_wins_over_pass(self) -> None:
        self.assertEqual(normalize_verdict("Escalate for approval to proceed"), "ESCALATE")

    def test_case_insensitivity(self) -> None:
        self.assertEqual(normalize_verdict("REFUSED"), "REFUSE")
        self.assertEqual(normalize_verdict("ESCALATE"), "ESCALATE")
        self.assertEqual(normalize_verdict("APPROVED"), "PASS")

    def test_none_input(self) -> None:
        self.assertEqual(normalize_verdict(None), "DRIFT")


if __name__ == "__main__":
    unittest.main()
