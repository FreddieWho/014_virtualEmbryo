"""Focused regression tests for numeric-only audit summaries."""
from __future__ import annotations

import unittest

from scripts.generate_audit import numeric_server_bests


def row(score, *, version="v0001", status="candidate", score_status="scored"):
    return {
        "board": "T1:val",
        "version": version,
        "method": "fixture",
        "status": status,
        "score_status": score_status,
        "server_score": score,
    }


class NumericServerBestsTest(unittest.TestCase):
    def test_registered_numeric_winner_is_included(self):
        result = numeric_server_bests([
            row("62.48"),
            row("66.7846", version="v0026", status="scored", score_status="registered"),
        ])
        self.assertEqual(result["T1:val"], (66.7846, "v0026", "fixture"))

    def test_existing_scored_winner_is_unchanged(self):
        result = numeric_server_bests([row("58.9887"), row("58.64", version="v0095")])
        self.assertEqual(result["T1:val"][0:2], (58.9887, "v0001"))

    def test_unscored_and_unknown_score_statuses_are_excluded(self):
        for score_status in ("score_pending", "invalidated_unsubmitted", "withdrawn", "unknown", ""):
            with self.subTest(score_status=score_status):
                self.assertEqual(numeric_server_bests([row("99", score_status=score_status)]), {})

    def test_invalidated_withdrawn_and_unknown_row_statuses_are_excluded(self):
        for status in ("invalidated", "invalidated_unsubmitted", "withdrawn", "void", "unknown", ""):
            for score_status in ("scored", "registered"):
                with self.subTest(status=status, score_status=score_status):
                    self.assertEqual(numeric_server_bests([row("99", status=status, score_status=score_status)]), {})

    def test_missing_or_nonfinite_scores_are_excluded(self):
        for score in ("", "not_a_score", None, "NaN", "Inf", "-Inf"):
            with self.subTest(score=score):
                self.assertEqual(numeric_server_bests([row(score)]), {})

    def test_numeric_maximum_does_not_apply_incumbent_tie_rule(self):
        result = numeric_server_bests([row("53.69", version="v0088"), row("53.74", version="v0089")])
        self.assertEqual(result["T1:val"][0:2], (53.74, "v0089"))

    def test_exact_numeric_tie_keeps_first_record(self):
        result = numeric_server_bests([row("53.74", version="v0089"), row("53.74", version="v0090")])
        self.assertEqual(result["T1:val"][1], "v0089")


if __name__ == "__main__":
    unittest.main()
