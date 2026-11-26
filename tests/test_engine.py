#!/usr/bin/env python3
"""Tests for the Weirdest Job Title entry.

Run from the build directory:

    python3 -m unittest discover -s tests -v

The tests verify the sealed gate (1-60 UTF-8 characters), that two
runs produce byte-identical output, that the OUTPUT_PATH override is
honoured, that the candidate pool is well-formed, and that the chosen
title passes the judge-criteria sanity checks (a few words naming an
odd job, stranger than ordinary work, funny on first read, sounding
like a real job, readable at a glance).
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parent.parent
MAIN_PY = BUILD_DIR / "main.py"


def load_main():
    """Import main.py as a module without running it."""
    spec = importlib.util.spec_from_file_location("weirdest_job_title", MAIN_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_program(output_path):
    """Run main.py once with OUTPUT_PATH set, returning the raw bytes."""
    env = dict(os.environ)
    env["OUTPUT_PATH"] = str(output_path)
    result = subprocess.run(
        [sys.executable, str(MAIN_PY)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, "main.py failed: %s" % result.stderr
    return output_path.read_bytes()


class TestGate(unittest.TestCase):
    def test_winner_is_1_to_60_chars(self):
        mod = load_main()
        winner = mod.select_winner()
        title = mod.validate(winner["title"])
        self.assertGreaterEqual(len(title), 1)
        self.assertLessEqual(len(title), 60)
        self.assertEqual(title.strip(), title)
        self.assertNotEqual(title.strip(), "")

    def test_winner_is_utf8(self):
        mod = load_main()
        title = mod.select_winner()["title"]
        title.encode("utf-8")

    def test_validate_rejects_blank_and_too_long(self):
        mod = load_main()
        with self.assertRaises(ValueError):
            mod.validate("")
        with self.assertRaises(ValueError):
            mod.validate("   ")
        with self.assertRaises(ValueError):
            mod.validate("x" * 61)

    def test_all_candidates_within_gate(self):
        mod = load_main()
        for candidate in mod.CANDIDATES:
            title = candidate["title"]
            self.assertGreaterEqual(len(title), 1, title)
            self.assertLessEqual(len(title), 60, title)


class TestPool(unittest.TestCase):
    def test_pool_is_valid(self):
        mod = load_main()
        self.assertTrue(mod.assert_pool_valid())

    def test_pool_titles_are_unique(self):
        mod = load_main()
        titles = [c["title"] for c in mod.CANDIDATES]
        self.assertEqual(len(set(titles)), len(titles))

    def test_every_candidate_scores_every_criterion_0_to_5(self):
        mod = load_main()
        for candidate in mod.CANDIDATES:
            for criterion in mod.CRITERIA:
                self.assertIn(criterion, candidate["scores"], (candidate["title"], criterion))
                score = candidate["scores"][criterion]
                self.assertIsInstance(score, int)
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 5)

    def test_every_candidate_has_a_rationale_per_criterion(self):
        mod = load_main()
        for candidate in mod.CANDIDATES:
            for criterion in mod.CRITERIA:
                self.assertIn(criterion, candidate["notes"], (candidate["title"], criterion))
                self.assertTrue(candidate["notes"][criterion].strip())

    def test_pool_rejects_a_bad_candidate(self):
        mod = load_main()
        bad = dict(mod.CANDIDATES[0])
        bad = {"title": bad["title"], "scores": dict(bad["scores"]), "notes": dict(bad["notes"])}
        bad["scores"]["funny_first_read"] = 9
        with self.assertRaises(ValueError):
            mod.assert_pool_valid(mod.CANDIDATES + (bad,))


class TestDeterminism(unittest.TestCase):
    def test_two_runs_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.txt"
            second = Path(tmp) / "second.txt"
            first_bytes = run_program(first)
            second_bytes = run_program(second)
            self.assertEqual(first_bytes, second_bytes)

    def test_output_path_override_is_honoured(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "entry.txt"
            data = run_program(target)
            self.assertTrue(target.exists())
            self.assertEqual(data.decode("utf-8"), "Senior Manager of Abandoned Shopping Carts")

    def test_output_is_exactly_the_title_nothing_else(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "entry.txt"
            data = run_program(target)
            self.assertEqual(data.decode("utf-8"), "Senior Manager of Abandoned Shopping Carts")
            self.assertNotIn(b"\n", data)

    def test_ranking_table_lists_winner_first(self):
        mod = load_main()
        table = mod.rubric_table()
        lines = table.splitlines()
        self.assertIn("Senior Manager of Abandoned Shopping Carts", lines[1])
        self.assertIn("24", lines[1])


class TestJudgeCriteria(unittest.TestCase):
    def test_winner_is_the_expected_title(self):
        mod = load_main()
        winner = mod.select_winner()
        self.assertEqual(winner["title"], "Senior Manager of Abandoned Shopping Carts")
        self.assertEqual(len(winner["title"]), 42)

    def test_winner_scores_high_on_every_criterion(self):
        mod = load_main()
        winner = mod.select_winner()
        scores = winner["scores"]
        for criterion in mod.CRITERIA:
            self.assertIn(criterion, scores)
            self.assertGreaterEqual(scores[criterion], 4, criterion)

    def test_winner_beats_every_other_candidate(self):
        mod = load_main()
        winner = mod.select_winner()
        for candidate in mod.CANDIDATES:
            if candidate is winner:
                continue
            self.assertTrue(mod.beats(winner, candidate), candidate["title"])

    def test_winner_beats_the_ordinary_controls(self):
        mod = load_main()
        winner = mod.select_winner()
        controls = [c for c in mod.CANDIDATES if c["title"] in ("Software Engineer", "Accountant")]
        self.assertEqual(len(controls), 2)
        for control in controls:
            self.assertLess(control["scores"]["weird_job_title"], 3)
            self.assertEqual(control["scores"]["stranger_than_ordinary"], 0)
            self.assertTrue(mod.beats(winner, control))

    def test_ranking_is_deterministic(self):
        mod = load_main()
        first = [c["title"] for c in mod.rank_candidates(mod.CANDIDATES)]
        second = [c["title"] for c in mod.rank_candidates(mod.CANDIDATES)]
        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), len(first))

    def test_winner_is_a_few_words_naming_an_odd_job(self):
        mod = load_main()
        title = mod.select_winner()["title"]
        words = title.split()
        self.assertGreaterEqual(len(words), 3)
        self.assertLessEqual(len(words), 8)


if __name__ == "__main__":
    unittest.main()
